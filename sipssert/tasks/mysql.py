#!/usr/bin/env python
##
## This file is part of the SIPssert Testing Framework project
## Copyright (C) 2023 OpenSIPS Solutions
##
## This program is free software: you can redistribute it and/or modify
## it under the terms of the GNU General Public License as published by
## the Free Software Foundation, either version 3 of the License, or
## (at your option) any later version.
##
## This program is distributed in the hope that it will be useful,
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
## GNU General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with this program. If not, see <http://www.gnu.org/licenses/>.
##

from sipssert.task import Task
import tarfile
import os
import shutil

class MysqlTask(Task):

    mysql_default_env = {"MYSQL_ALLOW_EMPTY_PASSWORD":"yes"}
    default_image = "mysql"
    default_daemon = True
    default_mount_point = "/docker-entrypoint-initdb.d"

    def __init__(self, test_dir, config):
        super().__init__(test_dir, config)
        tar_file = 'mysipsrvdata'
        self.untar(tar_file)
    
    def untar(self, tar_file):
        tar_file_path = os.path.join(os.getcwd(), f"{tar_file}.tar")
        mysql_dir = os.path.join(os.getcwd(), tar_file)
        if os.path.exists(mysql_dir):
            shutil.rmtree(mysql_dir)
        try:
            with tarfile.open(tar_file_path, 'r') as tar:
                tar.extractall(path=os.getcwd())
                self.log.info(f"extracted contents of {tar_file} to {os.getcwd()}")
        except tarfile.TarError as e:
            self.log.error(f"error extracting {tar_file}: {e}, maybe forget to put sipsrvdata.tar under test case file")

    def get_task_env(self):

        env_dict = self.mysql_default_env
        env_dict.update(super().get_task_env())

        if "root_password" in self.config:
            self.root_password = self.config["root_password"]

        if self.root_password:
            env_dict["MYSQL_ROOT_PASSWORD"] = self.root_password

        return env_dict

# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4
