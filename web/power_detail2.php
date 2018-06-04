<?php
include("vars.php");
$this_form = $_SERVER['PHP_SELF'];
$notimeframe = $_REQUEST["notimeframe"];
$start = $_REQUEST["start"];
$end = $_REQUEST["end"];
$bar = $_REQUEST["bar"];
/*
$userTimezone = new DateTimeZone('America/Denver');
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
	$myDateTimeStart = new DateTime(gmdate('Y-m-d') . " 00:00:00");
} else {
	$myDateTimeStart = new DateTime($start . " 00:00:00");
} 
$offset = $userTimezone->getOffset($myDateTimeStart);
$myInterval=DateInterval::createFromDateString((string)$offset . 'seconds');
$myDateTimeStart->sub($myInterval);
$resultStart = $myDateTimeStart->format('Y-m-d H:i:s');
*/
if ($end == "") {
	$myDateTimeEnd = new DateTime(date('Y-m-d') . " 00:00:00");
} else {
	if (strpos($end, ":") == true) {
		$myDateTimeEnd = new DateTime($end);
	} else {
		$myDateTimeEnd = new DateTime($end . " 00:00:00");
	}
}
if ($start == "") {
	$myDateTimeStart = new DateTime(date('Y-m-d') . " 00:00:00");
} else {
	if (strpos($start, ":") == true) {
		$myDateTimeStart = new DateTime($start);
	} else {
		$myDateTimeStart = new DateTime($start . " 00:00:00");
	}
} 
$resultStart = $myDateTimeStart->format('Y-m-d H:i:s');
$resultEnd = $myDateTimeEnd->format('Y-m-d H:i:s');
if ($notimeframe != "" || $end == "") {
	$resultEnd = "";
}
//echo "resultStart: $resultStart<BR>";
//echo "resultEnd: $resultEnd<BR>";
   // Connecting, selecting database
   //print ("connecting to $ip...<BR>");
   $conn = new PDO("mysql:host=$ip;dbname=$dbName", $username, $password);
   $conn->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);
   $data = "";
   //echo "<BR>bar: $bar<BR>";
   if ($conn) {
	//$current_date_utc = gmdate("Y-m-d");
	$current_date_utc = date("Y-m-d");
	$total_generated = 0;
	$total_used = 0;
	$total_net = 0;
	$counter = 0;
	if ($bar == "" && $resultEnd == "") {
		$query = "select * from sp_power where period>='$resultStart' order by period ASC"; 
	} else if ($bar != "") {
		$query = "select * from sp_power where period>='$resultStart' order by period DESC"; 
	} else {
		$query = "select * from sp_power where period>='$resultStart' and period<='$resultEnd' order by period ASC"; 
	}
	foreach ($conn->query($query) as $row) {
		$period = $row["period"];
		$generated = $row["generated"];
		$used = $row["used"];
		$net = $generated + $used;
		//$data = $data . "['$period', $generated, $used, $net],";
		if ($bar != "") {
			if ($counter < 11) {
				$data = $data . "['$period', $generated, $used, $net],";
			}
		} else {
			$data = $data . "['$period', $generated, $used, $net],";
		}
		$total_generated += $generated;
		$total_used += $used;
		$total_net += $net;
		$counter++;
	}
	if ($bar == "" && $resultEnd == "") {
		$query = "select energy_total from sp_raw2 where insert_timestamp>='$resultStart' and device_serial='$PVname' order by insert_timestamp ASC"; 
	} else if ($bar != "") {
		$query = "select energy_total from sp_raw2 where insert_timestamp>='$resultStart' and device_serial='$PVname' order by insert_timestamp ASC"; 
	} else {
		$query = "select energy_total from sp_raw2 where insert_timestamp>='$resultStart' and insert_timestamp<='$resultEnd' and device_serial='$PVname' order by insert_timestamp ASC"; 
	}
	$counter = 0;
	$first_row_energy = 0;
	$last_row_energy = 0;
	foreach ($conn->query($query) as $row) {
		if ($counter == 0) {
			$first_row_energy = $row["energy_total"];
		}
		$last_row_energy = $row["energy_total"];
		$counter++;
	}
	$energy_total = $last_row_energy - $first_row_energy;
	//echo "<BR>first_row: $first_row_energy<BR>last_row: $last_row_energy<BR>energy_total: $energy_total<BR>";
   }
   //$total_generated = round($total_generated * 0.08333333333, 3);
   //$total_used = round($total_used * 0.08333333333, 3);
   //$total_net = round($total_net * 0.08333333333, 3);
   $total_generated = round($total_generated, 3);
   $total_used = round($energy_total, 3);
   $total_net = $total_generated + $total_used;
   //echo "<BR>total_generated: $total_generated<BR>total_used: $total_used<BR>total_net: $total_net<BR>";
   if ($total_used < 0) {
	$to_from_grid = "To";
	$total_used = abs($total_used);
	$to_from_grid_color = "#145A32";
	$to_from_grid_image = "to_grid.png";
   	$total_from_solar_percent = round($total_used / $total_net * 100, 1) + 100;
	$to_from_grid_value = $total_net - $total_used;
	if ($to_from_grid_value < 0) {
		$to_from_grid_value = 0;
		$total_generated_pie_value = total_generated;
	} else {
		$to_from_grid_value = round($total_used / $total_net * 100, 1);
		$total_generated_pie_value = 100 - round($total_used / $total_net * 100, 1);
	}
   } else {
	$to_from_grid = "From";
	$to_from_grid_color = "yellow";
	//$to_from_grid_color = "#869C54";
	$to_from_grid_image = "from_grid.png";
	if ($total_generated > 0) {
   		$total_from_solar_percent = round($total_generated / $total_net * 100, 1);
	} else {
		$total_from_solar_percent = 0;
	}
	$to_from_grid_value = $total_used;
	$total_generated_pie_value = $total_generated;
   }
   //print("$data<BR>");
?>
    <!--Load the AJAX API-->
    <link href="CalendarControl.css" rel="stylesheet" type="text/css">
    <script src="CalendarControl.js" language="javascript"></script>
    <script type="text/javascript" src="https://www.gstatic.com/charts/loader.js"></script>
    <script type="text/javascript">
   
    // Load the Visualization API.
    google.charts.load('current', {packages: ['corechart', 'bar' , 'table']});
     
    // Set a callback to run when the Google Visualization API is loaded.
    google.charts.setOnLoadCallback(drawChart);
     
    function drawChart() {
      // Create our data table out of JSON data loaded from server.
      var pieData = google.visualization.arrayToDataTable([
	['Todays Eneregy Mix', 'kWh'],
	['From Solar', <?= $total_generated_pie_value ?>],
	['<?= $to_from_grid ?>  Grid', <?= $to_from_grid_value ?>]
	]);

      var tableData = new google.visualization.DataTable();
	tableData.addColumn('number', 'Total Energy Used');
	tableData.addColumn('number', 'From Solar');
	tableData.addColumn('number', 'From Grid');
	tableData.addRows([
		[ {v: <?= $total_used ?> , f: '<?= $total_used ?>' }, 
		  {v: <?= $total_generated ?> , f: '<?= $total_generated ?>' }, 
		  {v: <?= $total_net ?> , f: '<?= $total_net ?>' }]
	]);

	// Options
        var pieOptions = {
            legend: 'none',
            //title: 'Todays Energy Mix',
            width: 400,
            height: 250,
	    pieHole: 0.4,
	    pieSliceTextStyle: {color: 'black', bold: true, fontSize: 20},
	    //colors:['red','#004411'],
            slices: {
            	0: { color: 'green' },
            	1: { color: '<?= $to_from_grid_color ?>' }
            }
        };

      var barData = new google.visualization.DataTable();
	barData.addColumn('string', 'Period');
	barData.addColumn('number', 'Generated');
	barData.addColumn('number', 'To/From Grid');
	barData.addColumn('number', 'Used');
	barData.addRows([ <?= $data ?> ]);

	// Options
        var barOptions = {
            title: 'Power',
            width: 1000,
            height: 450,
            hAxis: {title: 'Period'},
            vAxis: {title: 'kW'},
        };

        var tableOptions = {
            showRowNumber: true,
            width: '100%',
            height: '100%',
        };

      // Instantiate and draw our chart, passing in some options.
      <?php
	if ($bar != "") {
      		echo "var barChart = new google.visualization.ColumnChart(document.getElementById('bar_div'));";
	} else {
      		echo "var barChart = new google.visualization.AreaChart(document.getElementById('bar_div'));";
	}
      ?>
      barChart.draw(barData, barOptions);
      var pieChart = new google.visualization.PieChart(document.getElementById('pie_div'));
      pieChart.draw(pieData, pieOptions);
      var table = new google.visualization.Table(document.getElementById('table_div'));
      table.draw(barData, tableOptions);
      //var table2 = new google.visualization.Table(document.getElementById('table2_div'));
      //table2.draw(tableData, tableOptions);
    }

    </script>

    <!--Table and divs that hold the pie charts-->
<FORM action= <?= $this_form ?>>
<table BORDER=0> 
<tr>
<TD valign=bottom>Start: <input name=start onfocus=showCalendarControl(this); type=text></TD>
<TD>-</TD>
<TD valign=bottom>End: <input name=end onfocus=showCalendarControl(this); type=text></TD>
<TD><input type=submit value="Change Timeframe"></TD>
</tr>
<tr>
<TD align=right><B><?= $resultStart ?></TD>
<TD>-</TD>
<TD><B><?= $resultEnd ?></TD>
</tr>
</table>
</FORM>
    <table class="columns">
      <tr>
        <td valign=top><div id="bar_div" style="border: 1px solid #ccc"></div></td>
        <td valign=top style="border: 1px solid #ccc">
	<TABLE>
		<TR><TD colspan=3 align=center><FONT SIZE=4><B>Today's Energy Mix</B></FONT></TD></TR>
		<TR><TD colspan=3><HR></TD></TR>
		<TR><TD colspan=2 align=center>
			<TABLE width=400>
				<TR>
					<TD>&nbsp;</TD>
					<TD><FONT SIZE=5>Solar</FONT></TD>
					<TD>&nbsp;&nbsp;&nbsp;</TD>
					<TD>&nbsp;&nbsp;&nbsp;</TD>
					<TD>&nbsp;&nbsp;&nbsp;</TD>
					<TD>&nbsp;&nbsp;&nbsp;</TD>
					<TD><FONT SIZE=5><B> <?= $total_from_solar_percent ?> %</B></FONT></TD>
				</TR>
			</TABLE>
		<TR><TD><div id="pie_div"></div></TD></TR>
		<TR><TD>
			<TABLE width=400>
				<TR><TD>&nbsp;</TD><TD>Total Energy Used:</TD><TD><B> <?= $total_net ?> kWh</B></TD>
				<TR><TD colspan=3><HR></TD></TR>
				<TR><TD><img src=from_solar.png></TD><TD>From Solar:</TD><TD><B> <?= $total_generated ?> kWh</B></TD>
				<TR><TD><img src=<?= $to_from_grid_image ?>></TD><TD><?= $to_from_grid ?> Grid:</TD><TD><B> <?= $total_used ?> kWh</B></TD>
				<TR valign=bottom><TD colspan=2><A HREF=power_detail.php>Details</A></TD></TR>
			</TABLE>
		</TD></TR>
	</TABLE>
	</td>
        <td><div id="table_div" style="border: 1px solid #ccc"></div></td>
        <td><div id="table2_div" style="border: 1px solid #ccc"></div></td>
      </tr>
    </table>
