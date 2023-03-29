/*
 * Copyright (c) 2023 Huawei Device Co., Ltd.
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

package manual

import (
	"context"
	"fmt"
	"fotff/tester"
	"fotff/utils"
	"github.com/sirupsen/logrus"
	"math/rand"
	"strings"
	"sync"
	"time"
)

type Tester struct {
	ResultLock sync.Mutex
}

func init() {
	rand.Seed(time.Now().UnixNano())
}

func NewTester() tester.Tester {
	ret := &Tester{}
	utils.ParseFromConfigFile("manual", ret)
	return ret
}

func (t *Tester) TaskName() string {
	return "manual_test"
}

func (t *Tester) Prepare(pkgDir string, device string, ctx context.Context) error {
	return nil
}

func (t *Tester) DoTestTask(deviceSN string, ctx context.Context) (ret []tester.Result, err error) {
	return t.DoTestCases(deviceSN, []string{"default"}, ctx)
}

func (t *Tester) DoTestCase(deviceSN, testCase string, ctx context.Context) (ret tester.Result, err error) {
	if deviceSN == "" {
		deviceSN = "default"
	}
	t.ResultLock.Lock()
	defer t.ResultLock.Unlock()
	var answer string
	for {
		fmt.Printf("please do testcase %s on device %s manually and type the test result, 'pass' or 'fail':\n", testCase, deviceSN)
		if _, err := fmt.Scanln(&answer); err != nil {
			logrus.Errorf("failed to scan result: %v", err)
			continue
		}
		switch strings.ToUpper(strings.TrimSpace(answer)) {
		case "PASS":
			return tester.Result{TestCaseName: testCase, Status: tester.ResultPass}, nil
		case "FAIL":
			return tester.Result{TestCaseName: testCase, Status: tester.ResultFail}, nil
		default:
		}
	}
}

func (t *Tester) DoTestCases(deviceSN string, testcases []string, ctx context.Context) (ret []tester.Result, err error) {
	for _, testcase := range testcases {
		r, err := t.DoTestCase(deviceSN, testcase, ctx)
		if err != nil {
			return nil, err
		}
		ret = append(ret, r)
	}
	return ret, nil
}
