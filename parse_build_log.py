#!/usr/bin/env python

import os
import sys
import errno
import time

import subprocess

TMP_DIR = "/tmp/parse_build_log"
TOP = "/media/system2/root/AOSP10"

def _module_path():
	if "__file__" in globals():
		return os.path.dirname(os.path.realpath(__file__))

	return ""

def parse(log):
	tmp_res = dict()
	with open(log, "r") as f:
		for line in f:
			if "[-Werror," in line and ":" in line:
				file = line.split(":")[0]
				error = line.split("[")[-1].split(",")[-1].split("]")[0]

				if not file in tmp_res:
					tmp_res[file] = []

				if not error in tmp_res[file]:
					tmp_res[file].append(error)
				else:
					continue

				#yield file, error
	return tmp_res

def warn2silence(warn):
	return "#pragma clang diagnostic ignored \"{warn}\"\n".format(warn = warn)


def main():
	#parse("/media/system2/root/AOSP10/error.log")
	#for file, error in parse(sys.argv[1]):
	#	#print(file, error)
	#	fname = os.path.basename(file)
	#	#with open("{tmp_dir}/{file}".format(tmp_dir = TMP_DIR, file = fname), "w") as out:
	#	#	with open("{top}/{file}".format(top = TOP, file = file), "r") as in:
	#	#
	#print(parse(sys.argv[1]))
	this_path = _module_path()
	errors_dict = parse(sys.argv[1])

	top_diff = "{top}/err.diff".format(top = TOP)
	diff_cmd = ["git", "diff", "--no-index"]

	if not os.path.exists(TMP_DIR):
		os.makedirs(TMP_DIR)

	if os.path.isfile(top_diff):
		os.remove(top_diff)

	OUT_DIR = "{top}/patches".format(top = TOP)

	with open(top_diff, "a+") as out_diff:
		for file in errors_dict.keys():
			#print(os.path.realpath(file), this_path)
			rfile = os.path.realpath(file).replace(this_path, "")

			in_file = "{top}{file}".format(top = TOP, file = rfile)
			#print(in_file, TOP, in_file.replace(TOP + "/", ""))
			out_file = "{tmp_dir}{file}".format(tmp_dir = TMP_DIR, file = rfile)
			out_dir = os.path.dirname(out_file)
			if not os.path.exists(out_dir):
				os.makedirs(out_dir)
			#print(in_file, out_file)
			with open(out_file, "w") as outf:
				with open(in_file, "r") as inf:
					buf_errs = []
					for err in errors_dict[file]:
						buf_errs.append(warn2silence(err))
					outf.writelines(buf_errs)
					outf.writelines(inf.readlines())

			fname = os.path.basename(file)
			diff_filename = "%s.diff" % fname
			tmp_diff_file = "{tmp_dir}/{file}".format(tmp_dir = TMP_DIR, file = diff_filename)

			if os.path.isfile(tmp_diff_file):
				os.remove(tmp_diff_file)

			if not os.path.exists(OUT_DIR):
				os.makedirs(OUT_DIR)

			with open(tmp_diff_file, "a+") as tmp_diff:
				print("processed file %s" % tmp_diff_file)
				p = subprocess.Popen(diff_cmd + [in_file, out_file], stdout = tmp_diff)
				p.communicate()
				p.wait()
				#time.sleep(0.6)
				tmp_diff.seek(0)
				out_diff.writelines(tmp_diff.readlines())

if __name__ == "__main__":
	main()
