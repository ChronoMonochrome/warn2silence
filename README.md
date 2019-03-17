# warn2silence
Turn Clang errors off in Android builds

This script parses Android build log for the Clang errors and tries to produce a diff file to turn these errors off, on a per-file basis.

# HowTo:

At the top of the Android source run:

```
source build/envsetup.sh
python warn2silence.py build_log.txt
```

If everything is ok, a file containing diffs will be generated. I can be used to patch the sources as follows:

```
patch -pX -i err.diff
```
