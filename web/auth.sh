#!/bin/bash
curl -H "Content-Type:application/json" -X POST -d '{
	"isPersistent":true,
	"password":"password",
	"username":"username"
}' https://monitor.us.sunpower.com/CustomerPortal/Auth/Auth.svc/Authenticate
