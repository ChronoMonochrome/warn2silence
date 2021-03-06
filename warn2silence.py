#!/usr/bin/env python
#
# Copyright (C) 2019 The Android Open Source Project
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
import sys
import errno
import time

import subprocess

TOP = None
TMP_DIR = "/tmp/parse_build_log"
PATCH_CMD = "patch -p{X} -i err.diff"
PNUM = "X"

"""class Error:
	def __init__(self, err_type, is_clang_error):
		self.err_type = err_type
		self.is_clang_error = is_clang_error"""

def _module_path():
	if "__file__" in globals():
		return os.path.dirname(os.path.realpath(__file__))

	return ""

def setup_env():
	global TOP, PNUM, PATCH_CMD
	if not "ANDROID_BUILD_TOP" in os.environ:
		usage("please run \"source build/envsetup.sh\" at the top of the Android source tree.")

	TOP = os.environ["ANDROID_BUILD_TOP"]
	PNUM = TOP.count("/") + 1
	PATCH_CMD = PATCH_CMD.format(X = PNUM)


def parse(log):
	res = dict()
	err_msg_dict = dict()
	with open(log, "r") as f:
		is_gcc_err = False
		is_clang_err = False
		for line in f:
			colon = (":" in line)
			closing_bracket = ("]" in line)
			common_err_ptr = colon and closing_bracket
			is_gcc_err = common_err_ptr and ("[-Werror=" in line)
			is_clang_err = common_err_ptr and ("[-Werror," in line)
			if is_clang_err:
				error = line.split("[")[-1].split(",")[-1].split("]")[0]
			elif is_gcc_err:
				error = "-W{}".format(line.split("[")[-1].split("=")[-1].split("]")[0])
			else:
				continue

			if is_gcc_err or is_clang_err:
				file = line.split(":")[0]
				if not file in res:
					res[file] = []

				error = [error, is_clang_err]

				if not error in res[file]:
					res[file].append(error)
				else:
					continue
	return res

def warn2silence(err_type, is_clang_error):
	compiler = "clang" if is_clang_error else "GCC"
	return "#pragma {compiler} diagnostic ignored \"{warn}\"\n"\
		.format(compiler = compiler, warn = err_type)


def usage(error = ""):
	global TOP, PNUM, PATCH_CMD

	print("usage: source build/envsetup.sh\n"
		  "	   python warn2silence.py build_log.txt\n" +
		  "	   {patch_cmd}\n".format(patch_cmd = PATCH_CMD) +
		  "{err}".format(err = ("\nerror: " + error) if error else ""))

	sys.exit()

def main(log_file):
	global TOP, PNUM, PATCH_CMD
	this_path = _module_path()
	errors_dict = parse(log_file)

	top_diff = "{top}/err.diff".format(top = TOP)
	diff_cmd = ["git", "diff", "--no-index"]

	if not os.path.exists(TMP_DIR):
		os.makedirs(TMP_DIR)

	if os.path.isfile(top_diff):
		os.remove(top_diff)

	OUT_DIR = "{top}/patches".format(top = TOP)

	with open(top_diff, "a+") as out_diff:
		for file in errors_dict.keys():
			rfile = os.path.realpath(file).replace(this_path, "").replace(TOP, "")

			in_file = "{top}{file}".format(top = TOP, file = rfile)
			if not os.path.exists(in_file):
				continue

			out_file = "{tmp_dir}{file}".format(tmp_dir = TMP_DIR, file = rfile)
			out_dir = os.path.dirname(out_file)

			if not os.path.exists(out_dir):
				os.makedirs(out_dir)

			with open(in_file, "r") as inf:
				with open(out_file, "w") as outf:
					buf_errs = []
					for err in errors_dict[file]:
						buf_errs.append(warn2silence(*err))
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
				tmp_diff.seek(0)
				out_diff.writelines(tmp_diff.readlines())

	pnum = (TOP.count("/") + 1) if TOP else "X"
	print("Ready! Now just run\n"
	      "       {patch_cmd}".format(patch_cmd = PATCH_CMD))


if __name__ == "__main__":
	setup_env()
	if (len(sys.argv) < 2):
		usage("no input file specified")

	main(sys.argv[1])
