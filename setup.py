#!/usr/bin/env python

import os
import subprocess
import tarfile
import shutil
import sysconfig

from setuptools import setup
from setuptools.command.build_ext import build_ext
from setuptools.extension import Extension


def _path_in_dir(relative_path):
    return os.path.abspath(os.path.join(os.path.dirname(__file__), relative_path))

def _dep_source_path(relative_path):
    return os.path.join(_path_in_dir("deps"), relative_path)

def _dep_build_path(relative_path):
    return os.path.join(_path_in_dir("_deps/build"), relative_path)

def _read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()


jq_lib_tarball_path = _dep_source_path("jq-1.7.tar.gz")
jq_lib_dir = _dep_build_path("jq-1.7")

oniguruma_version = "6.9.8"
oniguruma_lib_tarball_path = _dep_source_path("onig-{}.tar.gz".format(oniguruma_version))
oniguruma_lib_build_dir = _dep_build_path("onig-{}".format(oniguruma_version))
oniguruma_lib_install_dir = _dep_build_path("onig-install-{}".format(oniguruma_version))

class jq_with_deps_build_ext(build_ext):
    def run(self):
        if not os.path.exists(_dep_build_path(".")):
            os.makedirs(_dep_build_path("."))
        self._build_oniguruma()
        self._build_libjq()
        build_ext.run(self)

    def _build_oniguruma(self):
        self._build_lib(
            tarball_path=oniguruma_lib_tarball_path,
            lib_dir=oniguruma_lib_build_dir,
            commands=[
                ["./configure", "CFLAGS=-fPIC", "--prefix=" + oniguruma_lib_install_dir],
                ["make"],
                ["make", "install"],
            ])


    def _build_libjq(self):
        self._build_lib(
            tarball_path=jq_lib_tarball_path,
            lib_dir=jq_lib_dir,
            commands=[
                ["./configure", "CFLAGS=-fPIC -pthread", "--disable-maintainer-mode", "--with-oniguruma=" + oniguruma_lib_install_dir],
                ["make"],
            ])

    def _build_lib(self, tarball_path, lib_dir, commands):
        self._extract_tarball(
            tarball_path=tarball_path,
            lib_dir=lib_dir,
        )

        macosx_deployment_target = sysconfig.get_config_var("MACOSX_DEPLOYMENT_TARGET")
        if macosx_deployment_target:
            os.environ['MACOSX_DEPLOYMENT_TARGET'] = str(macosx_deployment_target)

        def run_command(args):
            print("Executing: %s" % ' '.join(args))
            subprocess.check_call(args, cwd=lib_dir)

        for command in commands:
            run_command(command)

    def _extract_tarball(self, tarball_path, lib_dir):
        if os.path.exists(lib_dir):
            shutil.rmtree(lib_dir)
        tarfile.open(tarball_path, "r:gz").extractall(_dep_build_path("."))


use_system_libs = bool(os.environ.get("JQPY_USE_SYSTEM_LIBS"))


if use_system_libs:
    jq_build_ext = build_ext
    link_args_deps = ["-ljq", "-lonig"]
    extra_objects = []
else:
    jq_build_ext = jq_with_deps_build_ext
    link_args_deps = []
    extra_objects = [
        os.path.join(jq_lib_dir, ".libs/libjq.a"),
        os.path.join(oniguruma_lib_install_dir, "lib/libonig.a"),
    ]


jq_extension = Extension(
    "jq",
    sources=["jq.c"],
    include_dirs=[os.path.join(jq_lib_dir, "src")],
    extra_link_args=["-lm"] + link_args_deps,
    extra_objects=extra_objects,
)

setup(
    name='jq',
    version='1.6.0',
    description='jq is a lightweight and flexible JSON processor.',
    long_description=_read("README.rst"),
    author='Michael Williamson',
    url='https://github.com/mwilliamson/jq.py',
    python_requires='>=3.5',
    license='BSD 2-Clause',
    ext_modules = [jq_extension],
    cmdclass={"build_ext": jq_build_ext},
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
    ],
)

