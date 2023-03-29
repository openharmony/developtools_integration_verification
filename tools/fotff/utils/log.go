/*
 * Copyright (c) 2022 Huawei Device Co., Ltd.
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

package utils

import (
	"fmt"
	"github.com/sirupsen/logrus"
	"os"
	"path/filepath"
	"runtime"
	"strings"
)

var LogFile *os.File
var StdoutFile *os.File
var osStdout, osStderr = os.Stdout, os.Stderr

func init() {
	if err := os.MkdirAll("logs", 0750); err != nil {
		logrus.Errorf("can not make logs dir: %v", err)
		return
	}
	logrus.SetOutput(os.Stdout)
	logrus.SetReportCaller(true)
	logrus.SetFormatter(&logrus.TextFormatter{
		ForceColors:     true,
		FullTimestamp:   true,
		TimestampFormat: "2006-01-02 15:04:05",
		CallerPrettyfier: func(f *runtime.Frame) (function string, file string) {
			funcName := strings.Split(f.Function, ".")
			fn := funcName[len(funcName)-1]
			_, filename := filepath.Split(f.File)
			return fmt.Sprintf("%s()", fn), fmt.Sprintf("%s:%d", filename, f.Line)
		},
	})
}

func ResetLogOutput() {
	logrus.Info("now log to os stdout...")
	logrus.SetOutput(osStdout)
	if LogFile != nil {
		LogFile.Close()
	}
	if StdoutFile != nil {
		StdoutFile.Close()
	}
	LogFile, StdoutFile, os.Stdout, os.Stderr = nil, nil, osStdout, osStderr
}

func SetLogOutput(pkg string) {
	file := filepath.Join("logs", pkg+".log")
	var f *os.File
	var err error
	if _, err = os.Stat(file); err == nil {
		f, err = os.OpenFile(file, os.O_RDWR|os.O_APPEND, 0666)
	} else {
		f, err = os.Create(file)
	}
	if err != nil {
		logrus.Errorf("failed to open new log file %s: %v", file, err)
		return
	}
	logrus.Infof("now log to %s", file)
	logrus.SetOutput(f)
	if LogFile != nil {
		LogFile.Close()
	}
	LogFile = f
	stdout := filepath.Join("logs", fmt.Sprintf("%s_stdout.log", pkg))
	if _, err = os.Stat(stdout); err == nil {
		f, err = os.OpenFile(stdout, os.O_RDWR|os.O_APPEND, 0666)
	} else {
		f, err = os.Create(stdout)
	}
	if err != nil {
		logrus.Errorf("failed to open new stdout log file %s: %v", stdout, err)
		return
	}
	if StdoutFile != nil {
		StdoutFile.Close()
	}
	StdoutFile, os.Stdout, os.Stderr = f, f, f
	logrus.Infof("re-directing stdout and stderr to %s...", stdout)
}
