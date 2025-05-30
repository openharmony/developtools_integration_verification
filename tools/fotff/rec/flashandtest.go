package rec

import (
	"context"
	"fotff/pkg"
	"fotff/tester"

	"github.com/sirupsen/logrus"
)

// FlashAndTestOptions specify which pkg.Manager and which tester to use to flash and test the specified version
type FlashAndTestOptions struct {
	M        pkg.Manager
	T        tester.Tester
	Version  string
	Device   string
	TestCase string
}

// FlashAndTest build and flash the given version to the specified device, then run the specified test cases
func FlashAndTest(ctx context.Context, opt *FlashAndTestOptions) error {
	// flash the specified version to the specified device
	if err := opt.M.Flash(opt.Device, opt.Version, ctx); err != nil {
		logrus.Errorf("Failed to flash version %s to device %s, error: %s", opt.Version, opt.Device, err.Error())
		return err
	}

	// prepare and run the specified test
	if err := opt.T.Prepare(opt.M.PkgDir(opt.Version), opt.Device, ctx); err != nil {
		logrus.Errorf("Failed to prepare test, error: %s", err.Error())
		return err
	}

	if opt.TestCase == "" {
		// run all test cases if the --testcase argument was not present
		results, err := opt.T.DoTestTask(opt.Device, ctx)
		if err != nil {
			logrus.Errorf("Failed to run all test cases on device %s, error: %s", opt.Device, err.Error())
			return err
		}

		// only mark test result as pass when all test cases passed
		var result tester.ResultStatus = tester.ResultPass
		for _, r := range results {
			logrus.Infof("Result for test case %s is %s", r.TestCaseName, r.Status)
			if r.Status == tester.ResultFail {
				result = tester.ResultFail
			}
		}

		logrus.Infof("Flash and test for all test cases done, result: %s", result)
		return nil
	} else {
		// otherwise run the specified test case
		result, err := opt.T.DoTestCase(opt.Device, opt.TestCase, ctx)
		if err != nil {
			logrus.Errorf("Failed to run test case %s on device %s, error: %s", opt.TestCase, opt.Device, err.Error())
			return err
		}

		logrus.Infof("Flash and test for test case %s done, result: %s", opt.TestCase, result)
		return nil
	}
}
