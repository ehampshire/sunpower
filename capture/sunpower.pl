#!/usr/bin/perl -W

use Net::Pcap;
use NetPacket::Ethernet;
use NetPacket::IP;
use NetPacket::TCP;
use NetPacket::UDP;
#use DateTime;
use POSIX qw/strftime/;

# setup logfile
my $logFileHandle;
my $timestamp = getLoggingTime();
my $logFileName = "/mnt/mydrive/logs/$timestamp.txt";

# setup pcap filter, so we see only the traffic we want
my $srcmacaddr = undef; # add the MAC address of your SunPower supervisor, if you find there is too much traffic without it
#my $srcmacaddr = c6ba4932b30a; # add the MAC address of your SunPower supervisor, if you find there is too much traffic without it
my $filterbysrcmacaddr = defined($srcmacaddr) ? (" && ether src " . $srcmacaddr) : "";
my $filtertext = "ip && tcp" . " && dst net 204.194.111.66 && dst port 80" . $filterbysrcmacaddr;

my $err;
# find the default interface (or you can set enif to a specific interface, if your sniff traffic comes to a NIC other than the default
my $enif = Net::Pcap::lookupdev(\$err);

printf("Finished setting up PCAP filter, starting to capture traffic...\n");

my $pcap = Net::Pcap::open_live($enif, 65535, 1, 512, \$err);

my $filter;
Net::Pcap::compile($pcap, \$filter, $filtertext, 1, 0);
Net::Pcap::setfilter($pcap, $filter);

Net::Pcap::loop($pcap, -1, packet_callback, "");

Net::Pcap::close($pcap);




# Then the filter is responsible for extracting the packet payloads:
sub packet_callback {
	my ($ignorerefcon, $hdr, $pkt) = @_;

	my $ethpkt = NetPacket::Ethernet->decode($pkt);
	my $ethprot = $ethpkt->{"type"};
	my $ethdata = $ethpkt->{"data"};

	if ($ethprot == NetPacket::Ethernet::ETH_TYPE_IP) {
		my $ippkt = NetPacket::IP->decode($ethdata);
		my $ipprot = $ippkt->{"proto"};
		my $ipdata = $ippkt->{"data"};

		if ($ipprot == NetPacket::IP::IP_PROTO_TCP) {
			my $tcpippkt = ($ipprot == NetPacket::IP::IP_PROTO_TCP) ? NetPacket::TCP->decode($ipdata) : NetPacket::UDP->decode($ipdata);
			my $data = $tcpippkt->{"data"};
			process_packet_payload($data);
		}
	}
}


# Then to process the packet payload:
sub process_packet_payload {
	my $data = $_[0];
	my @lines = split(/\n/, $data);
	my $temp = "";
	foreach my $line (@lines) {
		chomp($line);
		#if (($line =~ /^(140)\t(2017[0-3][0-9][0-9]{2}[0-9]{2}[0-9]{2}[0-9]{2})\t[0-9]+\t[^\s]+\t125\t([-+]?[0-9]*\.?[0-9]+)\t/) ||
			#($line =~ /^(130)\t(2017[0-3][0-9][0-9]{2}[0-9]{2}[0-9]{2}[0-9]{2})\t[0-9]+\t[^\s]+\t\t([-+]?[0-9]*\.?[0-9]+)\t/)  || 
			#($line =~ /^(100)\t/))
		#{
		if ($line =~ /^([0-9]+)\t/) {
			my $msg = $1;
			if ($msg == 140) { # this is a net metering message, and $value is net metering value in (IIRC) W averaged over the 5-minute interval
				# consumption = (corresponding production) + net
				#printf $value
				printf("net metering message (140):\n\t%s\n", $line);
				$temp = $temp . "$line\n";
			} elsif ($msg == 130) { # this is a production message, and $value is a production valuein (IIRC) W averaged over the 5-minute interval
				printf("production message (130):\n\t%s\n", $line);
				$temp = $temp . "$line\n";
			} elsif ($msg == 100) { # this is a control message / keep-alive
				printf("control message (100):\n\t%s\n", $line);
			} elsif ($msg == 102) { # this is a checksum message
				printf("checksum message (102):\n\t%s\n", $line);
			} else {
				printf("unknown message:\n\t%s\n", $line);
			}
		} else {
			printf("unmatched line:\n\t%s\n", $line);
		}
	}
	if ($temp ne "") {
		printf("We got either some 130 or 140 messages, writing them to the log: %s \n", $logFileName);
		openLog($logFileName);
		print $logFileHandle $temp;
		closeLog();
	}
}

sub getLoggingTime {
	#my $dt   = DateTime->now;   # Stores current date and time as datetime object
	#my $date = $dt->ymd;   # Retrieves date as a string in 'yyyy-mm-dd' format
	#my $time = $dt->hms;   # Retrieves time as a string in 'hh:mm:ss' format

	#my $nice_timestamp = "$date_$time";   # creates 'yyyy-mm-dd hh:mm:ss' string
	#my $nice_timestamp = strftime('%Y%m%d%H%M%S',localtime);
	my $nice_timestamp = strftime('%Y%m%d',localtime);
	return $nice_timestamp;
}

sub openLog {
	# setup log file
	my $logFileName = $_[0];
	open ($logFileHandle, ">>", $logFileName) or die "Cannot open $logFileName: $!";
	$| = 1;
	#printf("Opening logfile: %s\n", $logFileName);
}

sub closeLog {
	#printf("Closing logfile: %s\n", $logFileName);
	close ($logFileHandle);
}
