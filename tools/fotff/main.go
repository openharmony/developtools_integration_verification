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

package main

import (
	"context"
	"fotff/pkg"
	"fotff/pkg/dayu200"
	"fotff/pkg/gitee_build"
	"fotff/pkg/mock"
	"fotff/rec"
	"fotff/res"
	"fotff/tester"
	"fotff/tester/common"
	"fotff/tester/manual"
	testermock "fotff/tester/mock"
	"fotff/tester/pkg_available"
	"fotff/tester/smoke"
	"fotff/tester/xdevice"
	"fotff/utils"
	"os"
	"path/filepath"

	"github.com/sirupsen/logrus"
	"github.com/spf13/cobra"
)

var newPkgMgrFuncs = map[string]pkg.NewFunc{
	"mock":        mock.NewManager,
	"dayu200":     dayu200.NewManager,
	"gitee_build": gitee_build.NewManager,
}

var newTesterFuncs = map[string]tester.NewFunc{
	"mock":          testermock.NewTester,
	"manual":        manual.NewTester,
	"common":        common.NewTester,
	"xdevice":       xdevice.NewTester,
	"smoke":         smoke.NewTester,
	"pkg_available": pkg_available.NewTester,
}

var rootCmd *cobra.Command

func init() {
	m, t := initExecutor()
	rootCmd = &cobra.Command{
		Run: func(cmd *cobra.Command, args []string) {
			loop(m, t)
		},
	}
	runCmd := initRunCmd(m, t)
	flashCmd := initFlashCmd(m)
	testCmd := initTestCmd(m, t)
	rootCmd.AddCommand(runCmd, flashCmd, testCmd)
}

func initRunCmd(m pkg.Manager, t tester.Tester) *cobra.Command {
	var success, fail, testcase string
	runCmd := &cobra.Command{
		Use:   "run",
		Short: "bin-search in (success, fail] by do given testcase to find out the fist fail, and print the corresponding issue",
		RunE: func(cmd *cobra.Command, args []string) error {
			return fotff(m, t, success, fail, testcase)
		},
	}
	runCmd.PersistentFlags().StringVarP(&success, "success", "s", "", "success package directory")
	runCmd.PersistentFlags().StringVarP(&fail, "fail", "f", "", "fail package directory")
	runCmd.PersistentFlags().StringVarP(&testcase, "testcase", "t", "", "testcase name")
	runCmd.MarkPersistentFlagRequired("success")
	runCmd.MarkPersistentFlagRequired("fail")
	runCmd.MarkPersistentFlagRequired("testcase")
	return runCmd
}

func initFlashCmd(m pkg.Manager) *cobra.Command {
	var flashPkg, device string
	flashCmd := &cobra.Command{
		Use:   "flash",
		Short: "flash the given package",
		RunE: func(cmd *cobra.Command, args []string) error {
			return m.Flash(device, flashPkg, context.TODO())
		},
	}
	flashCmd.PersistentFlags().StringVarP(&flashPkg, "package", "p", "", "package directory")
	flashCmd.PersistentFlags().StringVarP(&device, "device", "d", "", "device sn")
	flashCmd.MarkPersistentFlagRequired("package")
	return flashCmd
}

func initTestCmd(m pkg.Manager, t tester.Tester) *cobra.Command {
	var targetPkg, device, testCase string
	testCmd := &cobra.Command{
		Use:   "test",
		Short: "build and flash and test the given package on the specified device",
		RunE: func(cmd *cobra.Command, args []string) error {
			opt := &rec.FlashAndTestOptions{
				M:        m,
				T:        t,
				Version:  targetPkg,
				Device:   device,
				TestCase: testCase,
			}
			return rec.FlashAndTest(context.TODO(), opt)
		},
	}
	testCmd.PersistentFlags().StringVarP(&targetPkg, "package", "p", "", "package directory")
	testCmd.PersistentFlags().StringVarP(&device, "device", "d", "", "target device sn")
	testCmd.PersistentFlags().StringVarP(&testCase, "testcase", "t", "", "test case to run")
	testCmd.MarkPersistentFlagRequired("package")
	testCmd.MarkPersistentFlagRequired("device")

	return testCmd
}

func main() {
	utils.EnablePprof()
	if err := rootCmd.Execute(); err != nil {
		logrus.Errorf("failed to execute: %v", err)
		os.Exit(1)
	}
}

func loop(m pkg.Manager, t tester.Tester) {
	data, _ := utils.ReadRuntimeData("last_handled.rec")
	var curPkg = string(data)
	for {
		utils.ResetLogOutput()
		if err := utils.WriteRuntimeData("last_handled.rec", []byte(curPkg)); err != nil {
			logrus.Errorf("failed to write last_handled.rec: %v", err)
		}
		logrus.Info("waiting for a newer package...")
		var err error
		curPkg, err = m.GetNewer(curPkg)
		if err != nil {
			logrus.Infof("get newer package err: %v", err)
			continue
		}
		utils.SetLogOutput(filepath.Base(curPkg))
		logrus.Infof("now flash %s...", curPkg)
		device := res.GetDevice()
		if err := m.Flash(device, curPkg, context.TODO()); err != nil {
			logrus.Errorf("flash package dir %s err: %v", curPkg, err)
			res.ReleaseDevice(device)
			continue
		}
		if err := t.Prepare(m.PkgDir(curPkg), device, context.TODO()); err != nil {
			logrus.Errorf("do test preperation for package %s err: %v", curPkg, err)
			continue
		}
		logrus.Info("now do test suite...")
		results, err := t.DoTestTask(device, context.TODO())
		if err != nil {
			logrus.Errorf("do test suite for package %s err: %v", curPkg, err)
			continue
		}
		for _, r := range results {
			logrus.Infof("do test case %s at %s done, result is %v", r.TestCaseName, device, r.Status)
		}
		logrus.Infof("now analysis test results...")
		toFotff := rec.HandleResults(t, device, curPkg, results)
		res.ReleaseDevice(device)
		rec.Analysis(m, t, curPkg, toFotff)
		rec.Save()
		rec.Report(curPkg, t.TaskName())
	}
}

func fotff(m pkg.Manager, t tester.Tester, success, fail, testcase string) error {
	issueURL, err := rec.FindOutTheFirstFail(m, t, testcase, success, fail)
	if err != nil {
		logrus.Errorf("failed to find out the first fail: %v", err)
		return err
	}
	logrus.Infof("the first fail found: %v", issueURL)
	return nil
}

func initExecutor() (pkg.Manager, tester.Tester) {
	//TODO load from config file
	var conf = struct {
		PkgManager string `key:"pkg_manager" default:"mock"`
		Tester     string `key:"tester" default:"mock"`
	}{}
	utils.ParseFromConfigFile("", &conf)
	newPkgMgrFunc, ok := newPkgMgrFuncs[conf.PkgManager]
	if !ok {
		logrus.Panicf("no package manager found for %s", conf.PkgManager)
	}
	newTesterFunc, ok := newTesterFuncs[conf.Tester]
	if !ok {
		logrus.Panicf("no tester found for %s", conf.Tester)
	}
	return newPkgMgrFunc(), newTesterFunc()
}
