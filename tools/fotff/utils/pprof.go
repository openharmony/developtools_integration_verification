package utils

import (
	"github.com/sirupsen/logrus"
	"net"
	"net/http"
	_ "net/http/pprof"
	"strconv"
)

func EnablePprof() {
	var cfg struct {
		Enable string `key:"enable" default:"true"`
		Port   string `key:"port" default:"80"`
	}
	ParseFromConfigFile("pprof", &cfg)
	if enable, _ := strconv.ParseBool(cfg.Enable); !enable {
		return
	}
	server := &http.Server{Addr: net.JoinHostPort("localhost", cfg.Port)}
	go func() {
		if err := server.ListenAndServe(); err != nil {
			logrus.Errorf("server.ListenAndServe returns error: %v", err)
		}
	}()
}
