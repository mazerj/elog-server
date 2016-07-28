-- MySQL dump 10.13  Distrib 5.5.33, for debian-linux-gnu (x86_64)
--
-- Host: sql    Database: mlabdata
-- ------------------------------------------------------
-- Server version	5.5.41-0+wheezy1

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `animal`
--

DROP TABLE IF EXISTS `animal`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `animal` (
  `ID` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `animal` varchar(255) DEFAULT NULL,
  `idno` varchar(255) DEFAULT NULL,
  `dob` date DEFAULT NULL,
  `living` int(1) DEFAULT 1,
  `user` varchar(10) DEFAULT NULL,
  `date` date DEFAULT NULL,
  `note` text,
  `locked` int(11) DEFAULT NULL,
  `tags` varchar(1024) DEFAULT NULL,
  `lastmod` varchar(255) DEFAULT NULL,
  PRIMARY KEY (`ID`),
  UNIQUE KEY `animal` (`animal`),
  UNIQUE KEY `idno` (`idno`)
) ENGINE=MyISAM AUTO_INCREMENT=8 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `attachment`
--

DROP TABLE IF EXISTS `attachment`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `attachment` (
  `ID` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `title` varchar(255) DEFAULT NULL,
  `user` varchar(10) DEFAULT NULL,
  `date` date DEFAULT NULL,
  `type` varchar(255) DEFAULT NULL,
  `note` text,
  `srctable` varchar(20) DEFAULT NULL,
  `srcID` int(11) unsigned DEFAULT NULL,
  `data` longblob,
  `locked` int(11) DEFAULT NULL,
  `tags` varchar(1024) DEFAULT NULL,
  `lastmod` varchar(255) DEFAULT NULL,
  UNIQUE KEY `attachmentID` (`ID`)
) ENGINE=MyISAM AUTO_INCREMENT=709 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `dfile`
--

DROP TABLE IF EXISTS `dfile`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `dfile` (
  `ID` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `exper` varchar(10) DEFAULT NULL,
  `animal` varchar(10) DEFAULT NULL,
  `date` date DEFAULT NULL,
  `user` varchar(10) DEFAULT NULL,
  `src` varchar(255) DEFAULT NULL,
  `filetype` varchar(20) DEFAULT NULL,
  `latency` float DEFAULT NULL,
  `winsize` float DEFAULT NULL,
  `crap` int(11) DEFAULT NULL,
  `preferred` int(11) DEFAULT NULL,
  `note` text,
  `attachlist` varchar(255) DEFAULT NULL,
  `locked` int(11) DEFAULT NULL,
  `tags` varchar(1024) DEFAULT NULL,
  `lastmod` varchar(255) DEFAULT NULL,
  UNIQUE KEY `dfileID` (`ID`),
  UNIQUE KEY `src` (`src`)
) ENGINE=MyISAM AUTO_INCREMENT=20305 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `exper`
--

DROP TABLE IF EXISTS `exper`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `exper` (
  `ID` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `exper` varchar(10) DEFAULT NULL,
  `animal` varchar(10) DEFAULT NULL,
  `dir` varchar(255) DEFAULT NULL,
  `date` date DEFAULT NULL,
  `time` varchar(11) DEFAULT NULL,
  `note` text,
  `locked` int(11) DEFAULT NULL,
  `deleted` int(11) DEFAULT NULL,
  `tags` varchar(1024) DEFAULT NULL,
  `lastmod` varchar(255) DEFAULT NULL,
  UNIQUE KEY `experID` (`ID`)
) ENGINE=MyISAM AUTO_INCREMENT=4218 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `session`
--

DROP TABLE IF EXISTS `session`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `session` (
  `ID` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `animal` varchar(10) DEFAULT NULL,
  `user` varchar(10) DEFAULT NULL,
  `computer` varchar(40) DEFAULT NULL,
  `date` date DEFAULT NULL,
  `restricted` int(11) DEFAULT NULL,
  `tested` int(11) DEFAULT NULL,
  `water_work` int(11) DEFAULT NULL,
  `water_sup` int(11) DEFAULT NULL,
  `dtb` double DEFAULT NULL,
  `dtb_ml` double DEFAULT NULL,
  `xdtb` double DEFAULT NULL,
  `xdtb_ml` double DEFAULT NULL,
  `fruit` varchar(255) DEFAULT NULL,
  `fruit_ml` int(11) DEFAULT NULL,
  `totalfluid` double DEFAULT NULL,
  `food` int(11) DEFAULT NULL,
  `weight` double DEFAULT NULL,
  `thweight` double DEFAULT NULL,
  `ncorrect` int(11) DEFAULT NULL,
  `ntrials` int(11) DEFAULT NULL,
  `health_stool` int(11) DEFAULT NULL,
  `health_urine` int(11) DEFAULT NULL,
  `health_skin` int(11) DEFAULT NULL,
  `health_pcv` int(11) DEFAULT NULL,
  `note` text,
  `locked` int(11) DEFAULT NULL,
  `tags` varchar(1024) DEFAULT NULL,
  `lastmod` varchar(255) DEFAULT NULL,
  UNIQUE KEY `noteID` (`ID`)
) ENGINE=MyISAM AUTO_INCREMENT=5306 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `unit`
--

DROP TABLE IF EXISTS `unit`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `unit` (
  `ID` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `experID` int(10) unsigned DEFAULT NULL,
  `exper` varchar(10) DEFAULT NULL,
  `unit` varchar(10) DEFAULT NULL,
  `animal` varchar(10) DEFAULT NULL,
  `date` date DEFAULT NULL,
  `well` varchar(11) DEFAULT NULL,
  `wellloc` varchar(255) DEFAULT NULL,
  `area` varchar(10) DEFAULT NULL,
  `hemi` char(1) DEFAULT NULL,
  `depth` int(11) DEFAULT NULL,
  `qual` float DEFAULT NULL,
  `rfx` float DEFAULT NULL,
  `rfy` float DEFAULT NULL,
  `rfr` float DEFAULT NULL,
  `latency` float DEFAULT NULL,
  `ori` float DEFAULT NULL,
  `color` varchar(20) DEFAULT NULL,
  `crap` int(11) DEFAULT NULL,
  `note` text,
  `locked` int(11) DEFAULT NULL,
  `tags` varchar(1024) DEFAULT NULL,
  `lastmod` varchar(255) DEFAULT NULL,
  PRIMARY KEY (`ID`),
  UNIQUE KEY `unitID` (`ID`)
) ENGINE=MyISAM AUTO_INCREMENT=2060 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2015-05-06 12:41:45
