package common

import (
	"context"
	"encoding/json"
	"errors"
	"fmt"
	"fotff/tester"
	"fotff/utils"
	"os"
	"path/filepath"
	"strings"

	"github.com/sirupsen/logrus"
)

const (
	testResultPass = "pass"
	testCaseFlag   = "--test-case"
	deviceFlag     = "--device"
)

// Tester is the common tester for most kinds of tests
type Tester struct {
	Tool       string `key:"tool"`
	Param      string `key:"param"`
	ResultPath string `key:"result_path"`
	ResultFile string `key:"result_file"`
}

// TestResult is the structure of the test result json file
type TestResult struct {
	TestCase string `json:"test_case"`
	Result   string `json:"result"`
}

func NewTester() tester.Tester {
	t := &Tester{}
	utils.ParseFromConfigFile("common", t)
	return t
}

func (t *Tester) TaskName() string {
	return "common_tester"
}

func (t *Tester) Prepare(version string, device string, ctx context.Context) error {
	return nil
}

// DoTestTask run all test cases on the specified device
func (t *Tester) DoTestTask(device string, ctx context.Context) ([]tester.Result, error) {
	args := strings.Split(t.Param, " ")
	if device != "" {
		args = append(args, []string{deviceFlag, device}...)
	}
	if err := utils.ExecContext(ctx, t.Tool, args...); err != nil {
		if errors.Is(err, context.Canceled) {
			return nil, err
		}
		logrus.Errorf("Failed to do test task on device %s, error: %s", device, err.Error())
		return nil, err
	}

	return t.processResult()
}

// DoTestCase run the specified test case on the specified device
func (t *Tester) DoTestCase(device string, testCase string, ctx context.Context) (tester.Result, error) {
	args := strings.Split(t.Param, " ")
	args = append(args, testCaseFlag)
	args = append(args, testCase)
	if device != "" {
		args = append(args, []string{deviceFlag, device}...)
	}
	defaultResult := tester.Result{}
	if err := utils.ExecContext(ctx, t.Tool, args...); err != nil {
		if errors.Is(err, context.Canceled) {
			return defaultResult, err
		}
		logrus.Errorf("Failed to do test case %s on device %s, error: %s", testCase, device, err.Error())
		return defaultResult, err
	}

	rs, err := t.processResult()
	if err != nil {
		return defaultResult, err
	}
	if len(rs) == 0 {
		return defaultResult, fmt.Errorf("failed to process test result: no test result found")
	}
	if rs[0].TestCaseName != testCase {
		return defaultResult, fmt.Errorf("failed to process test result: no matched test result found")
	}

	logrus.Infof("test case %s on device %s finished, the result is %s", testCase, device, rs[0].Status)
	return rs[0], nil
}

// DoTestCases run the specified test cases on the specified device
func (t *Tester) DoTestCases(device string, testCases []string, ctx context.Context) ([]tester.Result, error) {
	args := strings.Split(t.Param, " ")
	args = append(args, testCaseFlag)
	args = append(args, testCases...)
	if device != "" {
		args = append(args, []string{deviceFlag, device}...)
	}
	if err := utils.ExecContext(ctx, t.Tool, args...); err != nil {
		if errors.Is(err, context.Canceled) {
			return nil, err
		}
		logrus.Errorf("Failed to do test cases %v on device %s, error: %s", testCases, device, err.Error())
		return nil, err
	}

	return t.processResult()
}

// processResult parse the test result file
func (t *Tester) processResult() ([]tester.Result, error) {
	resultFile := filepath.Join(t.ResultPath, t.ResultFile)
	data, err := os.ReadFile(resultFile)
	if err != nil {
		logrus.Errorf("Failed to read from result file %s, error: %s", resultFile, err.Error())
		return nil, err
	}

	var result []TestResult
	if err := json.Unmarshal(data, &result); err != nil {
		logrus.Errorf("Failed to unmarshal test result %s into json array, error: %s", string(data), err.Error())
		return nil, err
	}

	var ret []tester.Result
	for _, r := range result {
		if r.Result == testResultPass {
			ret = append(ret, tester.Result{TestCaseName: r.TestCase, Status: tester.ResultPass})
		} else {
			ret = append(ret, tester.Result{TestCaseName: r.TestCase, Status: tester.ResultFail})
		}
	}
	return ret, nil
}
