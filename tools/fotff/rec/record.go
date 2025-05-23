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

package rec

import (
	"context"
	"encoding/json"
	"fotff/pkg"
	"fotff/tester"
	"fotff/utils"
	"github.com/sirupsen/logrus"
	"time"
)

var Records = make(map[string]Record)

func init() {
	data, err := utils.ReadRuntimeData("records.json")
	if err != nil {
		return
	}
	if err := json.Unmarshal(data, &Records); err != nil {
		logrus.Errorf("unmarshal records err: %v", err)
	}
}

func Save() {
	data, err := json.MarshalIndent(Records, "", "\t")
	if err != nil {
		logrus.Errorf("marshal records err: %v", err)
		return
	}
	if err := utils.WriteRuntimeData("records.json", data); err != nil {
		logrus.Errorf("save records err: %v", err)
		return
	}
	logrus.Infof("save records successfully")
}

func HandleResults(t tester.Tester, dev string, pkgName string, results []tester.Result) []string {
	var passes, fails []tester.Result
	for _, result := range results {
		switch result.Status {
		case tester.ResultPass:
			passes = append(passes, result)
		case tester.ResultFail:
			fails = append(fails, result)
		}
	}
	handlePassResults(pkgName, passes)
	return handleFailResults(t, dev, pkgName, fails)
}

func handlePassResults(pkgName string, results []tester.Result) {
	for _, result := range results {
		logrus.Infof("recording [%s] as a success, the lastest success package is [%s]", result.TestCaseName, pkgName)
		Records[result.TestCaseName] = Record{
			UpdateTime:       time.Now().Format("2006-01-02 15:04:05"),
			Status:           tester.ResultPass,
			LatestSuccessPkg: pkgName,
			EarliestFailPkg:  "",
			FailIssueURL:     "",
		}
	}
}

func handleFailResults(t tester.Tester, dev string, pkgName string, results []tester.Result) []string {
	var fotffTestCases []string
	for _, result := range results {
		if record, ok := Records[result.TestCaseName]; ok && record.Status != tester.ResultPass {
			logrus.Warnf("test case %s had failed before, skip handle it", result.TestCaseName)
			continue
		}
		status := tester.ResultFail
		for i := 0; i < 3; i++ {
			r, err := t.DoTestCase(dev, result.TestCaseName, context.TODO())
			if err != nil {
				logrus.Errorf("failed to do test case %s: %v", result.TestCaseName, err)
				continue
			}
			logrus.Infof("do testcase %s at %s done, result is %s", r.TestCaseName, dev, r.Status)
			if r.Status == tester.ResultPass {
				logrus.Warnf("testcase %s result is %s", r.TestCaseName, tester.ResultOccasionalFail)
				status = tester.ResultOccasionalFail
				break
			}
		}
		if status == tester.ResultFail && Records[result.TestCaseName].LatestSuccessPkg != "" && Records[result.TestCaseName].EarliestFailPkg == "" {
			fotffTestCases = append(fotffTestCases, result.TestCaseName)
		}
		Records[result.TestCaseName] = Record{
			UpdateTime:       time.Now().Format("2006-01-02 15:04:05"),
			Status:           status,
			LatestSuccessPkg: Records[result.TestCaseName].LatestSuccessPkg,
			EarliestFailPkg:  pkgName,
			FailIssueURL:     "",
		}
	}
	return fotffTestCases
}

func Analysis(m pkg.Manager, t tester.Tester, pkgName string, testcases []string) {
	for i, testcase := range testcases {
		record := Records[testcase]
		logrus.Infof("%s failed, the lastest success package is [%s], earliest fail package is [%s], now finding out the first fail...", testcase, record.LatestSuccessPkg, pkgName)
		issueURL, err := FindOutTheFirstFail(m, t, testcase, record.LatestSuccessPkg, pkgName, testcases[i+1:]...)
		if err != nil {
			logrus.Errorf("failed to find out the first fail issue, err: %v", err)
			issueURL = err.Error()
		}
		logrus.Infof("recording %s as a failure, the lastest success package is [%s], the earliest fail package is [%s], fail issue URL is [%s]", testcase, record.LatestSuccessPkg, pkgName, issueURL)
		Records[testcase] = Record{
			UpdateTime:       time.Now().Format("2006-01-02 15:04:05"),
			Status:           tester.ResultFail,
			LatestSuccessPkg: record.LatestSuccessPkg,
			EarliestFailPkg:  pkgName,
			FailIssueURL:     issueURL,
		}
	}
}
