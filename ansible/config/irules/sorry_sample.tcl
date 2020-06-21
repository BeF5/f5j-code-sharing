when HTTP_REQUEST {
  set VSPool /Common/pool_webservers
  if { [active_members $VSPool] < 1 } {
	HTTP::respond 200 content "
<html>
<head>
    <title>We'll be back!</title>
    <meta http-equiv='Refresh' content='1'>
</head>
<body>
    <h2>Hi there! Thanks for stopping by.</h2>
    <h3>We're making some changes on the site and expect to be back in a couple of hours.<br><br>See you there!</h3>
</body>
</html>
"
  } else {
		pool $VSPool
  }
}