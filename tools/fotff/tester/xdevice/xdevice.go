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

package xdevice

import (
	"context"
	"crypto/md5"
	"encoding/xml"
	"errors"
	"fmt"
	"fotff/tester"
	"fotff/utils"
	"github.com/sirupsen/logrus"
	"math/rand"
	"os"
	"path/filepath"
	"strings"
	"time"
)

const enableTestModeScript = `mount -o rw,remount /; param set persist.ace.testmode.enabled 1; param set persist.sys.hilog.debug.on true; sed -i 's/enforcing/permissive/g' /system/etc/selinux/config; sync; reboot`

type Tester struct {
	Task          string `key:"task" default:"acts"`
	Config        string `key:"config" default:"./config/user_config.xml"`
	TestCasesPath string `key:"test_cases_path" default:"./testcases"`
	ResourcePath  string `key:"resource_path" default:"./resource"`
}

type Report struct {
	XMLName   xml.Name `xml:"testsuites"`
	TestSuite []struct {
		TestCase []struct {
			Name   string `xml:"name,attr"`
			Result string `xml:"result,attr"`
		} `xml:"testcase"`
	} `xml:"testsuite"`
}

func init() {
	rand.Seed(time.Now().UnixNano())
}

func NewTester() tester.Tester {
	ret := &Tester{}
	utils.ParseFromConfigFile("xdevice", ret)
	return ret
}

func (t *Tester) TaskName() string {
	return t.Task
}

func (t *Tester) Prepare(pkgDir string, device string, ctx context.Context) (err error) {
	logrus.Info("for xdevice test, try to enable test mode...")
	if err := utils.HdcShell(enableTestModeScript, device, ctx); err != nil {
		return err
	}
	time.Sleep(20 * time.Second) // usually, it takes about 20s to reboot into OpenHarmony
	if connected := utils.WaitHDC(device, ctx); !connected {
		logrus.Errorf("enable test mode at device %s done, but boot unnormally, hdc connection fail", device)
		return fmt.Errorf("enable test mode at device %s done, but boot unnormally, hdc connection fail", device)
	}
	time.Sleep(10 * time.Second) // wait 10s more to ensure system has been started completely
	logrus.Infof("enable test mode at device %s successfully", device)
	return nil
}

func (t *Tester) DoTestTask(deviceSN string, ctx context.Context) (ret []tester.Result, err error) {
	reportDir := fmt.Sprintf("%X", md5.Sum([]byte(fmt.Sprintf("%d", rand.Int()))))
	args := []string{"-m", "xdevice", "run", t.Task, "-c", t.Config, "-tcpath", t.TestCasesPath, "-respath", t.ResourcePath, "-rp", reportDir}
	if deviceSN != "" {
		args = append(args, "-sn", deviceSN)
	}
	if err := utils.ExecContext(ctx, "python", args...); err != nil {
		if errors.Is(err, context.Canceled) {
			return nil, err
		}
		logrus.Errorf("do test suite fail: %v", err)
		return nil, err
	}
	return t.readReport(reportDir)
}

func (t *Tester) DoTestCase(deviceSN, testCase string, ctx context.Context) (ret tester.Result, err error) {
	reportDir := fmt.Sprintf("%X", md5.Sum([]byte(fmt.Sprintf("%d", rand.Int()))))
	args := []string{"-m", "xdevice", "run", "-l", testCase, "-c", t.Config, "-tcpath", t.TestCasesPath, "-respath", t.ResourcePath, "-rp", reportDir}
	if deviceSN != "" {
		args = append(args, "-sn", deviceSN)
	}
	if err := utils.ExecContext(ctx, "python", args...); err != nil {
		if errors.Is(err, context.Canceled) {
			return ret, err
		}
		logrus.Errorf("do test case %s fail: %v", testCase, err)
		return ret, err
	}
	r, err := t.readReport(reportDir)
	if len(r) == 0 {
		return ret, fmt.Errorf("read latest report err, no result found")
	}
	if r[0].TestCaseName != testCase {
		return ret, fmt.Errorf("read latest report err, no matched result found")
	}
	logrus.Infof("do testcase %s at %s done, result is %s", r[0].TestCaseName, deviceSN, r[0].Status)
	return r[0], nil
}

func (t *Tester) DoTestCases(deviceSN string, testcases []string, ctx context.Context) (ret []tester.Result, err error) {
	reportDir := fmt.Sprintf("%X", md5.Sum([]byte(fmt.Sprintf("%d", rand.Int()))))
	args := []string{"-m", "xdevice", "run", "-l", strings.Join(testcases, ";"), "-c", t.Config, "-tcpath", t.TestCasesPath, "-respath", t.ResourcePath, "-rp", reportDir}
	if deviceSN != "" {
		args = append(args, "-sn", deviceSN)
	}
	if err := utils.ExecContext(ctx, "python", args...); err != nil {
		if errors.Is(err, context.Canceled) {
			return ret, err
		}
		logrus.Errorf("do test cases %v fail: %v", testcases, err)
		return ret, err
	}
	return t.readReport(reportDir)
}

func (t *Tester) readReport(reportDir string) (ret []tester.Result, err error) {
	data, err := os.ReadFile(filepath.Join("reports", reportDir, "summary_report.xml"))
	if err != nil {
		logrus.Errorf("read report xml fail: %v", err)
		return nil, err
	}
	var report Report
	err = xml.Unmarshal(data, &report)
	if err != nil {
		logrus.Errorf("unmarshal report xml fail: %v", err)
		return nil, err
	}
	for _, s := range report.TestSuite {
		for _, c := range s.TestCase {
			var status tester.ResultStatus
			if c.Result == "true" {
				status = tester.ResultPass
			} else {
				status = tester.ResultFail
			}
			ret = append(ret, tester.Result{TestCaseName: c.Name, Status: status})
		}
	}
	return ret, err
}
