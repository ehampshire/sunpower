<?php
header("Cache-Control: no-store, no-cache, must-revalidate, max-age=0");
header("Cache-Control: post-check=0, pre-check=0", false);
header("Pragma: no-cache");
	$timeframe = "2017-01-20 22:40:00";
	if (!empty($timeframe)) {
		print ("<TABLE>");
		print ("<TR>");
		print ("<TD><B>Search: </B></TD>");
		print ("<TD>$timeframe</TD>");
		print ("</TR>");
		d = new DateTime($timeframe);
		$d->sub(new DateInterval('PT5M'));
		$new_timeframe = date_format($d, 'Y-M-d H:i:s');
		print ("new_timeframe: $new_timeframe");
		/*
		//$parsed = date_parse("$timeframe -5 minute");
		//print_r($parsed);
		//$parsed = date('Y-M-d H:i:s', strtotime('-5 minute', strtotime($timeframe)));
		//$parsed = date_format(strtotime('-5 minute', strtotime($timeframe)), 'Y-M-d H:i:s');
		//print ("parsed: $parsed);

		$splitter = split(":", $timeframe);
		print_r($splitter);
		if ($splitter[1] != "00") {
			$new_minute = $splitter[1] - 5;
			$new_timeframe = $splitter[0] + $new_minute + $splitter[2];
		} else {
			$new_minute = "55";
			$splitter2 = split(" ", $splitter[0]);
			print_r($splitter2);
			$new_hour = $splitter2[1] - 1;
			$new_timeframe = $new_hour + $new_minute + $splitter[2];
		}
		print ("new_timeframe: $new_timeframe);
		*/
		print ("</TABLE>");
	}
?>
