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

package tester

import "context"

type ResultStatus string

const (
	ResultPass           = `pass`
	ResultOccasionalFail = `occasional_fail`
	ResultFail           = `fail`
)

type Result struct {
	TestCaseName string
	Status       ResultStatus
}

type Tester interface {
	// TaskName returns the name of task which DoTestTask execute.
	TaskName() string
	// Prepare do some test preparations for one certain package
	Prepare(pkgDir string, device string, ctx context.Context) error
	// DoTestTask do a full test on given device.
	DoTestTask(device string, ctx context.Context) ([]Result, error)
	// DoTestCase do a single testcase on given device.
	DoTestCase(device string, testCase string, ctx context.Context) (Result, error)
	// DoTestCases do testcases on given device.
	DoTestCases(device string, testcases []string, ctx context.Context) ([]Result, error)
}

type NewFunc func() Tester
