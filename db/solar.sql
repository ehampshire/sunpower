-- phpMyAdmin SQL Dump
-- version 4.6.3
-- https://www.phpmyadmin.net/
--
-- Host: localhost
-- Generation Time: Mar 28, 2017 at 01:51 PM
-- Server version: 5.5.51-MariaDB
-- PHP Version: 5.5.38

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;


create database if not exists solar;

--
-- Database: `solar`
--

-- --------------------------------------------------------

--
-- Table structure for table `sp_energy`
--

CREATE TABLE `sp_energy` (
  `id` bigint(20) NOT NULL,
  `period` datetime NOT NULL,
  `per_produced` float NOT NULL,
  `per_used` float NOT NULL,
  `per_net` float NOT NULL,
  `cum_produced` int(11) NOT NULL,
  `cum_used` int(11) NOT NULL,
  `cum_net` int(11) NOT NULL
) ENGINE=MyISAM DEFAULT CHARSET=latin1;

-- --------------------------------------------------------

--
-- Table structure for table `sp_power`
--

CREATE TABLE `sp_power` (
  `id` bigint(20) NOT NULL,
  `period` datetime NOT NULL,
  `generated` float NOT NULL,
  `used` float NOT NULL
) ENGINE=MyISAM DEFAULT CHARSET=latin1;

-- --------------------------------------------------------

--
-- Table structure for table `sp_raw_production`
--

CREATE TABLE `sp_raw_production` (
  `id` bigint(20) UNSIGNED NOT NULL,
  `message_type` int(11) NOT NULL,
  `src_timestamp` datetime NOT NULL,
  `insert_timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `device_serial` varchar(15) NOT NULL,
  `device_description` varchar(50) NOT NULL,
  `watts` float NOT NULL,
  `v1` float NOT NULL,
  `v2` float NOT NULL,
  `v3` float NOT NULL,
  `v4` float NOT NULL,
  `v5` float NOT NULL,
  `v6` float NOT NULL,
  `v7` float NOT NULL,
  `v8` float NOT NULL,
  `v9` int(11) NOT NULL
) ENGINE=MyISAM DEFAULT CHARSET=latin1;

--
-- Indexes for dumped tables
--

--
-- Indexes for table `sp_energy`
--
ALTER TABLE `sp_energy`
  ADD PRIMARY KEY (`id`);

--
-- Indexes for table `sp_power`
--
ALTER TABLE `sp_power`
  ADD PRIMARY KEY (`id`);

--
-- Indexes for table `sp_raw_production`
--
ALTER TABLE `sp_raw_production`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `tableid` (`id`),
  ADD KEY `device_serial_indx` (`device_serial`);

--
-- AUTO_INCREMENT for dumped tables
--

--
-- AUTO_INCREMENT for table `sp_energy`
--
ALTER TABLE `sp_energy`
  MODIFY `id` bigint(20) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=1906;
--
-- AUTO_INCREMENT for table `sp_power`
--
ALTER TABLE `sp_power`
  MODIFY `id` bigint(20) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=22561;
--
-- AUTO_INCREMENT for table `sp_raw_production`
--
ALTER TABLE `sp_raw_production`
  MODIFY `id` bigint(20) UNSIGNED NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=239813;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
