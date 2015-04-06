-- call with something like:
--    mysqladmin -h${HOST} -u${USER} -p${PASS} create ${DB} <<EOF

use mlabdata;

CREATE TABLE `attachment` (
  `attachmentID` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `title` varchar(255) DEFAULT NULL,
  `user` varchar(10) DEFAULT NULL,
  `date` date DEFAULT NULL,
  `type` varchar(255) DEFAULT NULL,
  `note` text,
  `srctable` varchar(20) DEFAULT NULL,
  `srcID` int(11) unsigned NOT NULL,
  `data` longblob,
  `locked` int(11) DEFAULT NULL,
  `tags` varchar(1024) DEFAULT NULL,
  `lastmod` varchar(255) DEFAULT NULL,
  UNIQUE KEY `attachmentID` (`attachmentID`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;

CREATE TABLE `dfile` (
  `dfileID` int(10) unsigned NOT NULL AUTO_INCREMENT,
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
  UNIQUE KEY `dfileID` (`dfileID`),
  UNIQUE KEY `src` (`src`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;

CREATE TABLE `exper` (
  `experID` int(10) unsigned NOT NULL AUTO_INCREMENT,
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
  UNIQUE KEY `experID` (`experID`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;

CREATE TABLE `session` (
  `sessionID` int(10) unsigned NOT NULL AUTO_INCREMENT,
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
  UNIQUE KEY `noteID` (`sessionID`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;

CREATE TABLE `unit` (
  `unitID` int(10) unsigned NOT NULL AUTO_INCREMENT,
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
  PRIMARY KEY (`unitID`),
  UNIQUE KEY `unitID` (`unitID`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;

CREATE TABLE `animal` (
  `animalID` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `animal` varchar(255) DEFAULT NULL,
  `idno` varchar(255) DEFAULT NULL,
  `user` varchar(10) DEFAULT NULL,
  `date` date DEFAULT NULL,
  `note` text,
  `locked` int(11) DEFAULT NULL,
  `tags` varchar(1024) DEFAULT NULL,
  `lastmod` varchar(255) DEFAULT NULL,
  PRIMARY KEY `animalID` (`animalID`),
  UNIQUE KEY `animal` (`animal`),
  UNIQUE KEY `idno` (`idno`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;
