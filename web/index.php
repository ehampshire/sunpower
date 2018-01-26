<?php
header("Cache-Control: no-store, no-cache, must-revalidate, max-age=0");
header("Cache-Control: post-check=0, pre-check=0", false);
header("Pragma: no-cache");
?>
<link rel="stylesheet" href="main.css" type="text/css">
<?php
include("vars.php");

$lifetime_color = "blue";
function print_panel_table_row($panel_array, $device_array_values) {
	$lifetime_color = "blue";
	$tolerance = "1200";
	$current_time_utc = gmdate("Y-m-d H:i:s");
	$utc_epoch = strtotime($current_time_utc);
	//print ("utc_epoch: $utc_epoch<BR>");
	print("<TR>");		
	print("<TABLE BORDER=1>");
	foreach ($panel_array as $i => $value) {
		print("<TH colspan=5>$value</TH>");
	}
	print("<TR>");
	foreach ($panel_array as $i => $value) {
		$this_device_last_update = $device_array_values["$value"][0];
		$this_device_calculated_watts = $device_array_values["$value"][1];
		$this_device_temp = $device_array_values["$value"][2];
		$this_device_calculated_kwh = $device_array_values["$value"][3];
		$lifetime_watts = $device_array_values["$value"][4];
		if ($this_device_calculated_watts > 0) { 
       			$colour = "green"; 
   		} elseif ($this_device_calculated_watts <= 0) { 
       			$colour = "red"; 
    		}
		$last_update_epoch = strtotime($this_device_last_update);
		//print ("last_update_epoch: $last_update_epoch<BR>");
		$difference = $utc_epoch - $last_update_epoch;
		//print ("difference: $difference<BR>");
		if ($difference > $tolerance) {
       			$tcolour = "red"; 
   		} else {
       			$tcolour = ""; 
    		}
		print("<TD align=center><FONT COLOR=$tcolour>$this_device_last_update</FONT></TD>");
		print("<TD align=center><FONT COLOR=$colour>$this_device_calculated_watts W</FONT></TD>");
		print("<TD align=center><FONT COLOR=$colour>$this_device_calculated_kwh kWh</FONT></TD>");
		$f = round(($this_device_temp * 9/5) + 32, 1);
		print("<TD align=center><FONT COLOR=$colourv1>$f&deg;</FONT></TD>");
		print("<TD align=center><FONT COLOR=$lifetime_color>$lifetime_watts</FONT></TD>");
	}
	print("</TR>");		
	print("</TABLE>");		

}

$notimeframe = $_REQUEST["notimeframe"];
$start = $_REQUEST["start"];
$end = $_REQUEST["end"];
$bar = $_REQUEST["bar"];
//$userTimezone = new DateTimeZone('America/Denver');
$userTimezone = new DateTimeZone($myTimeZone);
$gmtTimezone = new DateTimeZone('GMT');
if ($end == "") {
	$myDateTimeEnd = new DateTime(gmdate('Y-m-d') . " 00:00:00");
} else {
	$myDateTimeEnd = new DateTime($end . " 00:00:00");
}
$offset = $userTimezone->getOffset($myDateTimeEnd);
$myInterval=DateInterval::createFromDateString((string)$offset . 'seconds');
$myDateTimeEnd->sub($myInterval);
$resultEnd = $myDateTimeEnd->format('Y-m-d H:i:s');
if ($start == "") {
	//$myDateTimeStart = new DateTime(gmdate('Y-m-d') . " 00:00:00");
	$myDateTimeStart = new DateTime(date('Y-m-d') . " 00:00:00");
} else {
	$myDateTimeStart = new DateTime($start . " 00:00:00");
} 
$offset = $userTimezone->getOffset($myDateTimeStart);
$myInterval=DateInterval::createFromDateString((string)$offset . 'seconds');
$myDateTimeStart->sub($myInterval);
$resultStart = $myDateTimeStart->format('Y-m-d H:i:s');
if ($notimeframe != "" || $end == "") {
	$resultEnd = "";
}

$r = $_REQUEST["r"];
$timeframe = $_REQUEST["timeframe"];
$this_form = $_SERVER['PHP_SELF'];
if (!empty($r)) {
	$refresh_rate = $r;
} else {
	$refresh_rate = 60;
}

print("<TABLE BORDER=0>");
print("<TR>");
print("<TD valign=top>");
if ($r != "(disabled)") {
	print("<meta http-equiv=\"refresh\" content=\"$refresh_rate;url=$this_form?r=$refresh_rate\">");
}
print("<FORM ACTION=$this_form METHOD=GET>");
print("<INPUT TYPE=text NAME=r size=4>");
print("<INPUT TYPE=submit VALUE=\"Set Refresh (s)\"></FORM>");
print("</TD>");
?>

<TD valign=top>
<FORM ACTION=<?= $this_form ?>METHOD=GET>
<INPUT TYPE=submit VALUE="CLEAR Timeframe"></FORM>
</TD>
<TD valign=top>
<FORM action= <?= $this_form ?>>
Start: <input name=start onfocus=showCalendarControl(this); type=text></TD>
<TD valign=top>-</TD>
<TD valign=top>End: <input name=end onfocus=showCalendarControl(this); type=text></TD>
<TD valign=top><input type=submit value="Change Timeframe"></FORM></TD>
</tr>
<tr>
<TD>&nbsp;</TD>
<TD>&nbsp;</TD>
<TD align=right valign=top><B><?= $resultStart ?></TD>
<TD valign=top>-</TD>
<TD valign=top><B><?= $resultEnd ?></TD>
</tr>
</table>

<?php
print("</TABLE>");
print("</TR>");

   // Connecting, selecting database
   //print ("connecting to $ip...<BR>");
   $conn = new PDO("mysql:host=$ip;dbname=$dbName", $username, $password);
   $conn->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);

   if ($conn) {
	$query = "select count(*) from sp_raw_production";
	foreach ($conn->query($query) as $row) {
		$total_rows = $row["count(*)"];
	}
	
print ("<TABLE BORDER=0><TR valign=center><TD>");
print ("<TABLE BORDER=0><TR><TD>");
	print ("<TABLE BORDER=0>");
	print("<TR><TD align=right><B>Refresh:</B></TD><TD>$refresh_rate s</TD></TR>");
	print("<TR><TD align=right><B>Rows:</B></TD><TD>$total_rows</TD></TR>");
	$current_time_utc = gmdate("Y-m-d H:i:s");
	//date_default_timezone_set('UTC');
	//$blah = date_default_timezone_get();
	//print ("date_default_timezone_get(): $blah");
	$current_local_time = date("Y-m-d H:i:s");
	print ("<TR>");
	print ("<TD align=right><B>UTC: </B></TD>");
	print ("<TD>$current_time_utc</TD>");
	print ("</TR>");
	print ("<TR>");
	print ("<TD align=right><B>Local: </B></TD>");
	print ("<TD>$current_local_time</TD>");
	print ("</TR>");
	// example timeframe: 2017-01-20 22:40:00
	if (!empty($timeframe)) {
		print ("<TR>");
		print ("<TD><B>Search: </B></TD>");
		print ("<TD>$timeframe</TD>");
		print ("</TR>");
		$orig_timeframe = $timeframe;
		$d = new DateTime($timeframe);
		$d->sub(new DateInterval('PT5M'));
		$new_timeframe = date_format($d, 'Y-m-d H:i:s');
		//print("new_timeframe: $new_timeframe");
		$timeframe = $new_timeframe;
	}
	print ("<TR><TD>&nbsp;</TD></TR>");
	print ("</TABLE>");
	if (empty($timeframe)) {
		print ("Last 5 minutes view:");
	}
	print ("<TABLE BORDER=0>");
	
	$query = "select distinct(device_serial) from sp_raw_production where message_type='130'";
	$device_array = array();
	$device_array_values = array();
	$i = 0;
	foreach ($conn->query($query) as $row) {
		$this_device_serial = $row["device_serial"];
		$device_array[$i++] = $this_device_serial;
	}
	//print_r($device_array);
			// PV monitor
			$this_device_serial = $PVname;
			$this_net = 0;
			print ("<TR>");
			print ("<TABLE BORDER=1>");
			$query2 = "select max(src_timestamp) from sp_raw_production where device_serial='$this_device_serial'";
			foreach ($conn->query($query2) as $row) {
				$this_device_last_update =  $row["max(src_timestamp)"];
				$PVmonitor_timestamp = $this_device_last_update;
				if (!empty($timeframe)) {
					$query3 = "SELECT watts, src_timestamp FROM sp_raw_production WHERE device_serial='$this_device_serial' and src_timestamp>='$timeframe' limit 2";
				} else {
					$query3 = "SELECT watts, src_timestamp FROM sp_raw_production WHERE device_serial='$this_device_serial' order by src_timestamp DESC limit 2";
				}
				$calculated_watts = 0;	
				$counter = 0;
				foreach ($conn->query($query3) as $row) {
					if ($counter == 0) {
						$this_device_last_update = $row["src_timestamp"];	
					}
					$this_watts[$counter++] =  $row["watts"];
				}
				//print_r($this_watts);
				if (!empty($timeframe)) {
					$temper = $this_watts[1] - $this_watts[0];
				} else {
					$temper = $this_watts[0] - $this_watts[1];
				}
				$calculated_kwH = round($temper, 5);
				$temper = $calculated_kwH / 0.08333333333;
				$calculated_watts = round($temper, 5);
				$this_net = $calculated_watts;
				print ("<TH colspan=4>$this_device_serial</TH>");
				print ("<TR>");
				print ("<TD>$this_device_last_update</TD>");
				if ($calculated_watts > 0) { 
       					$colour = "red"; 
   				} elseif ($calculated_watts < 0) { 
       					$colour = "green"; 
    				}
				print ("<TD align=center><FONT color=$colour>$calculated_watts kW</FONT></TD>");
				print ("<TD align=center><FONT color=$colour>$calculated_kwH kWh</FONT></TD>");
				print ("<TD align=center><FONT color=$lifetime_color>$this_watts[0]</FONT></TD>");
				print ("</TR>");
			}		
			print ("</TABLE>");
			print ("</TR>");
	//print ("</TABLE>");
	$total_production = 0;
	$total_v1 = 0;
	$total_v2 = 0;
	// panels
	foreach ($device_array as $i => $value) {
		$this_device_serial = $value;
		if (!empty($timeframe)) {
			//print("Adjusting timeframe to: $timeframe");
			$query2 = "select max(src_timestamp) from sp_raw_production where device_serial='$this_device_serial' and src_timestamp='$timeframe'";
			//$query2 = "select max(src_timestamp) from sp_raw_production where device_serial='$this_device_serial'";
		} else {
			$query2 = "select max(src_timestamp) from sp_raw_production where device_serial='$this_device_serial'";
		}
		//print ("<TR>");
		foreach ($conn->query($query2) as $row) {
			$this_device_last_update =  $row["max(src_timestamp)"];
			if (!empty($timeframe)) {
				//$query3 = "SELECT watts, src_timestamp, v1, v2, v7 FROM sp_raw_production WHERE device_serial='$this_device_serial' and src_timestamp>='$timeframe' limit 2";
				$query3 = "SELECT watts, src_timestamp, v1, v2, v7 FROM sp_raw_production WHERE device_serial='$this_device_serial' and src_timestamp>='$new_timeframe' OR src_timestamp>='$orig_timeframe' limit 2";
			} else {
				$query3 = "SELECT watts, src_timestamp, v1, v2, v7 FROM sp_raw_production WHERE device_serial='$this_device_serial' order by src_timestamp DESC limit 2";
			}
			$calculated_watts = 0;	
			$calculated_v1 = 0;	
			$calculated_kwH = 0;
			$end_timestamp = 0;	
			$counter = 0;
			foreach ($conn->query($query3) as $row) {
				if ($counter == 0) {
					$this_device_last_update = $row["src_timestamp"];	
					$temp = $row["v7"];	
				} else {
					if (!empty($timeframe)) {
						$end_timestamp = $row["src_timestamp"];
					}
				}
				$this_watts[$counter] =  $row["watts"];
				$this_v1[$counter] =  $row["v1"];
				$this_v2[$counter] =  $row["v2"];
				$counter++;
			}
			//print_r($this_watts);
			if (!empty($timeframe)) {
				/*
				print("new_timeframe: $new_timeframe");
				print("orig_timeframe: $orig_timeframe");
				print("counter: $counter");
				print("this_device_serial: $this_device_last_update ");
				print("this_device_last_update: $this_device_last_update ");
				print("end_timestamp: $end_timestamp ");
				print("this_watts[0]: $this_watts[0] ");
				print("this_watts[1]: $this_watts[1] ");
				print("<BR>");
				*/
				if ($new_timeframe == $this_device_last_update && $orig_timeframe == $end_timestamp) {
					$temper = $this_watts[1] - $this_watts[0];
				} else {
					$temper = 0;
				}
				//$temper = $this_watts[1] - $this_watts[0];
			} else {
				$temper = $this_watts[0] - $this_watts[1];
			}
			if ($PVmonitor_timestamp != $this_device_last_update) {
				$calculated_watts = 0;
				$calculated_kwH = 0;
			} else {
				$calculated_kwH = round($temper, 5);
				$temper2 = $calculated_kwH / 0.08333333333;
				$calculated_watts2 = round($temper2, 5);
				$temper = ($calculated_kwH / 0.08333333333) * 1000;
				$calculated_watts = round($temper, 5);
				$total_production += $calculated_watts2;
			}
			//print ("<TD align=center>$this_device_serial</TD>");
			//print ("<TD>$this_device_last_update</TD>");
			//print ("<TD align=center>$calculated_watts</TD>");
			//print ("<TD>$total_production</TD>");
			$device_array_values[$this_device_serial] = array($this_device_last_update, $calculated_watts, $temp, $calculated_kwH, $this_watts[0]);
			
		}
		//print ("</TR>");		
	}
	//print_r($device_array_values);
	print ("<TABLE BORDER=0>");
	print ("<TR><TD align=right><B>Currently Producing:</B></TD>");
	if ($total_production > 0) { 
       		$colour = "green"; 
   	} elseif ($total_production < 0) { 
       		$colour = "red"; 
    	}
	print ("<TD align=left><FONT color=$colour>$total_production</FONT> kW</TD></TR>");
	$total_consumption = $this_net + $total_production;
	if ($total_consumption > 0) { 
       		$colour = "red"; 
   	} elseif ($total_consumption < 0) { 
       		$colour = "green"; 
    	}
	print ("<TR><TD align=right><B>Total Consumption:</B></TD>");
	print ("<TD align=left><FONT color=$colour>$total_consumption</FONT> kW</TD></TR>");
	/*
	print ("<TR><TD align=right><B>Total v1:</B></TD>");
	print ("<TD align=center><FONT color=$colour1>$total_v1</FONT></TD></TR>");
	print ("<TR><TD align=right><B>Total v2:</B></TD>");
	print ("<TD align=center><FONT color=$colour2>$total_v2</FONT></TD></TR>");
	*/
	//print ("<TR><TD>&nbsp;</TD></TR>");
	//include("gauge.php");
	//print ("</TABLE>");
	//print("</TD>");
	//print("<TD>");
	include("todays_production2.php");
	//include("power_detail.php?bar=true");
	print("</TD></TR></TABLE>");

	print("<BR>");

	print ("<TR>");
	print ("<TABLE BORDER=1>");
	print ("<TH colspan=5>Device Serial</TH>");
	print ("<TR>");
	print ("<TD>Last Update (UTC)</TD>");
	print ("<TD>Last Production (W)</TD>");
	print ("<TD>Last Production (kWh)</TD>");
	print ("<TD>Temperature&deg; (F)</TD>");
	print ("<TD><FONT COLOR=blue>Lifetime Production (kWh)</FONT></TD>");
	print ("</TR>");
	print ("</TABLE>");
	print ("</TR>");
	print ("<TR><TD>&nbsp;</TD></TR>");

	print_panel_table_row($first_row, $device_array_values);
	print ("<TR><TD>&nbsp;</TD></TR>");

	print_panel_table_row($second_row, $device_array_values);
	print ("<TR><TD>&nbsp;</TD></TR>");

	print_panel_table_row($third_row, $device_array_values);

	print ("<TR><TD>&nbsp;</TD></TR>");
	print ("</TABLE>");

   } else {
	   print("failed to connect!");
   }

?>



