/*
SQLyog Ultimate v12.4.1 (64 bit)
MySQL - 5.7.30-log : Database - manga_extractor
*********************************************************************
*/

/*!40101 SET NAMES utf8 */;

/*!40101 SET SQL_MODE=''*/;

/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;
CREATE DATABASE /*!32312 IF NOT EXISTS*/`manga_extractor` /*!40100 DEFAULT CHARACTER SET utf8 */;

USE `manga_extractor`;

/*Table structure for table `exemplo_textos` */

DROP TABLE IF EXISTS `exemplo_textos`;

CREATE TABLE `exemplo_textos` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `id_volume` int(11) NOT NULL,
  `sequencia` int(4) DEFAULT NULL,
  `texto` longtext COLLATE utf8mb4_unicode_ci,
  `posicao_x1` double DEFAULT NULL,
  `posicao_y1` double DEFAULT NULL,
  `posicao_x2` double DEFAULT NULL,
  `posicao_y2` double DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `exemplo_volumes_exemplo_textos_fk` (`id_volume`),
  CONSTRAINT `exemplo_volumes_exemplo_textos_fk` FOREIGN KEY (`id_volume`) REFERENCES `exemplo_volumes` (`id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

/*Data for the table `exemplo_textos` */

/*Table structure for table `exemplo_volumes` */

DROP TABLE IF EXISTS `exemplo_volumes`;

CREATE TABLE `exemplo_volumes` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `manga` longtext COLLATE utf8mb4_unicode_ci NOT NULL,
  `volume` int(4) NOT NULL,
  `capitulo` double NOT NULL,
  `is_extra` tinyint(1) DEFAULT NULL,
  `nome_pagina` varchar(250) COLLATE utf8mb4_unicode_ci NOT NULL,
  `numero_pagina` int(11) DEFAULT NULL,
  `linguagem` varchar(4) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `hash_pagina` varchar(250) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `scan` varchar(250) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `is_raw` tinyint(1) DEFAULT NULL,
  `is_processado` tinyint(1) DEFAULT '0',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

/*Data for the table `exemplo_volumes` */

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;
