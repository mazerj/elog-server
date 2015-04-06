use mlabdata;

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
