<?php
include("vars.php");
   // Connecting, selecting database
   //print ("connecting to $ip...<BR>");
   $conn = new PDO("mysql:host=$ip;dbname=$dbName", $username, $password);
   $conn->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);
   $data = "";
   if ($conn) {
	$query = "select * from sp_power order by period DESC limit 10";
	foreach ($conn->query($query) as $row) {
		$period = $row["period"];
		$generated = $row["generated"];
		$used = $row["used"];
		$net = $generated + $used;
		//print("['$period', $generated, $used, $net],");
		$data = $data . "['$period', $generated, $used, $net],";
	}
   }
//print("$data<BR>");
?>
    <!--Load the AJAX API-->
    <script type="text/javascript" src="https://www.gstatic.com/charts/loader.js"></script>
    <script type="text/javascript">
   
    // Load the Visualization API.
    google.charts.load('current', {packages: ['corechart']});
     
    // Set a callback to run when the Google Visualization API is loaded.
    google.charts.setOnLoadCallback(drawChart);
     
    function drawChart() {
      // Create our data table out of JSON data loaded from server.
      //var data = new google.visualization.DataTable(jsonData);
      var data = new google.visualization.DataTable();
	data.addColumn('string', 'Period');
	data.addColumn('number', 'Generated');
	data.addColumn('number', 'Used');
	data.addColumn('number', 'Net');
	data.addRows([ <?= $data ?> ]);

	// Options
        var chartOptions = {
            title: 'Power',
            width: 1000,
            height: 400,
        };

        var tableOptions = {
            showRowNumber: true,
            width: 1000,
            height: 400,
        };

      // Instantiate and draw our chart, passing in some options.
      var chart = new google.visualization.ColumnChart(document.getElementById('chart_div'));
      chart.draw(data, chartOptions);
      var table = new google.visualization.Table(document.getElementById('table_div'));
      table.draw(data, tableOptions);
    }

    </script>

    <!--Table and divs that hold the pie charts-->
    <table class="columns">
      <tr>
        <td><div id="chart_div" style="border: 1px solid #ccc"></div></td>
        <td><div id="table_div" style="border: 1px solid #ccc"></div></td>
      </tr>
    </table>
