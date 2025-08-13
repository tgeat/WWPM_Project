CREATE DATABASE  IF NOT EXISTS `water_report` /*!40100 DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci */ /*!80016 DEFAULT ENCRYPTION='N' */;
USE `water_report`;
-- MySQL dump 10.13  Distrib 8.0.42, for Win64 (x86_64)
--
-- Host: localhost    Database: water_report
-- ------------------------------------------------------
-- Server version	9.3.0

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!50503 SET NAMES utf8 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `bao_type`
--

DROP TABLE IF EXISTS `bao_type`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `bao_type` (
  `id` int NOT NULL AUTO_INCREMENT,
  `bao_typeid` varchar(45) COLLATE utf8mb4_general_ci NOT NULL,
  `room_id` varchar(45) COLLATE utf8mb4_general_ci NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=34 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `bao_type`
--

LOCK TABLES `bao_type` WRITE;
/*!40000 ALTER TABLE `bao_type` DISABLE KEYS */;
INSERT INTO `bao_type` VALUES (28,'水报','21'),(29,'油报','21'),(30,'水报','23'),(31,'油报','23');
/*!40000 ALTER TABLE `bao_type` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `daily_report`
--

DROP TABLE IF EXISTS `daily_report`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `daily_report` (
  `report_id` bigint NOT NULL AUTO_INCREMENT,
  `well_id` bigint NOT NULL,
  `report_date` date NOT NULL,
  `injection_mode` varchar(20) DEFAULT NULL,
  `prod_hours` tinyint unsigned DEFAULT NULL,
  `trunk_pressure` decimal(4,1) DEFAULT NULL,
  `oil_pressure` decimal(4,1) DEFAULT NULL,
  `casing_pressure` decimal(4,1) DEFAULT NULL,
  `wellhead_pressure` decimal(4,1) DEFAULT NULL,
  `plan_inject` decimal(6,2) DEFAULT NULL,
  `actual_inject` decimal(6,2) DEFAULT NULL,
  `remark` varchar(100) DEFAULT NULL,
  `meter_stage1` decimal(10,2) DEFAULT NULL,
  `meter_stage2` decimal(10,2) DEFAULT NULL,
  `meter_stage3` decimal(10,2) DEFAULT NULL,
  PRIMARY KEY (`report_id`),
  UNIQUE KEY `uk_well_date` (`well_id`,`report_date`),
  CONSTRAINT `fk_report_well` FOREIGN KEY (`well_id`) REFERENCES `well` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=56 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='注水井日报';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `daily_report`
--

LOCK TABLES `daily_report` WRITE;
/*!40000 ALTER TABLE `daily_report` DISABLE KEYS */;
INSERT INTO `daily_report` VALUES (50,67,'2025-07-18','',NULL,NULL,NULL,NULL,NULL,NULL,NULL,'',NULL,NULL,NULL),(51,68,'2025-07-18','1',0,0.0,0.0,0.0,0.0,0.00,0.00,'水报测试1',0.00,0.00,0.00),(52,73,'2025-07-18','',NULL,NULL,NULL,NULL,NULL,NULL,NULL,'',NULL,NULL,NULL),(54,67,'2025-07-19','2',2,2.0,2.0,2.0,2.0,2.00,2.00,'2',2.00,2.00,2.00),(55,68,'2025-07-19',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL);
/*!40000 ALTER TABLE `daily_report` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `formula_datas`
--

DROP TABLE IF EXISTS `formula_datas`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `formula_datas` (
  `id` int NOT NULL AUTO_INCREMENT,
  `formula` varchar(255) COLLATE utf8mb4_general_ci DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=18 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `formula_datas`
--

LOCK TABLES `formula_datas` WRITE;
/*!40000 ALTER TABLE `formula_datas` DISABLE KEYS */;
INSERT INTO `formula_datas` VALUES (10,'波动范围=油压+24'),(11,'油量=油压*3'),(12,'液量/斗数（功图）=合量斗数-A2冲程'),(13,'液量/斗数（60/流量计）=套压*4'),(14,'和=油压+套压'),(15,'时间=油压+3'),(16,'产油=有效排液冲程/2'),(17,'日产油=套压*3');
/*!40000 ALTER TABLE `formula_datas` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `meter_room`
--

DROP TABLE IF EXISTS `meter_room`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `meter_room` (
  `id` int NOT NULL AUTO_INCREMENT,
  `team_id` int NOT NULL,
  `room_no` varchar(10) NOT NULL COMMENT '间号，如“104号”“ZS”',
  `is_injection_room` tinyint(1) DEFAULT '0' COMMENT '0=计量间 1=注水间',
  `is_oil` varchar(45) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_team_roomNo` (`team_id`,`room_no`),
  CONSTRAINT `fk_room_team` FOREIGN KEY (`team_id`) REFERENCES `prod_team` (`team_id`)
) ENGINE=InnoDB AUTO_INCREMENT=25 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='计量间 / 注水间';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `meter_room`
--

LOCK TABLES `meter_room` WRITE;
/*!40000 ALTER TABLE `meter_room` DISABLE KEYS */;
INSERT INTO `meter_room` VALUES (21,22,'110',0,NULL),(23,24,'测试111',0,NULL);
/*!40000 ALTER TABLE `meter_room` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `oil_well_reports`
--

DROP TABLE IF EXISTS `oil_well_reports`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `oil_well_reports` (
  `id` int NOT NULL AUTO_INCREMENT,
  `well_id` bigint DEFAULT NULL,
  `create_time` date DEFAULT NULL,
  `well_code` varchar(20) DEFAULT NULL,
  `platform` varchar(10) DEFAULT NULL,
  `oil_pressure` varchar(20) DEFAULT NULL,
  `casing_pressure` varchar(20) DEFAULT NULL,
  `back_pressure` varchar(20) DEFAULT NULL,
  `time_sign` varchar(20) DEFAULT NULL,
  `total_bucket_sign` varchar(10) DEFAULT NULL,
  `total_bucket` varchar(10) DEFAULT NULL,
  `press_data` varchar(255) DEFAULT NULL,
  `prod_hours` varchar(255) DEFAULT NULL,
  `a2_stroke` varchar(255) DEFAULT NULL,
  `a2_frequency` varchar(255) DEFAULT NULL,
  `work_stroke` varchar(255) DEFAULT NULL,
  `effective_stroke` varchar(255) DEFAULT NULL,
  `fill_coeff_test` varchar(255) DEFAULT NULL,
  `lab_water_cut` varchar(255) DEFAULT NULL,
  `reported_water` varchar(255) DEFAULT NULL,
  `fill_coeff_liquid` varchar(255) DEFAULT NULL,
  `last_tubing_time` varchar(255) DEFAULT NULL,
  `pump_diameter` varchar(255) DEFAULT NULL,
  `block` varchar(255) DEFAULT NULL,
  `transformer` varchar(255) DEFAULT NULL,
  `remark` varchar(255) DEFAULT NULL,
  `liquid_per_bucket` varchar(255) DEFAULT NULL,
  `sum_value` varchar(255) DEFAULT NULL,
  `liquid1` varchar(255) DEFAULT NULL,
  `production_coeff` varchar(255) DEFAULT NULL,
  `a2_24h_liquid` varchar(255) DEFAULT NULL,
  `liquid2` varchar(255) DEFAULT NULL,
  `oil_volume` varchar(255) DEFAULT NULL,
  `fluctuation_range` varchar(255) DEFAULT NULL,
  `shutdown_time` varchar(255) DEFAULT NULL,
  `theory_diff` varchar(255) DEFAULT NULL,
  `theory_displacement` varchar(255) DEFAULT NULL,
  `k_value` varchar(255) DEFAULT NULL,
  `daily_liquid` varchar(255) DEFAULT NULL,
  `daily_oil` varchar(255) DEFAULT NULL,
  `well_times` varchar(255) DEFAULT NULL,
  `production_time` varchar(255) DEFAULT NULL,
  `total_oil` varchar(255) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=54 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `oil_well_reports`
--

LOCK TABLES `oil_well_reports` WRITE;
/*!40000 ALTER TABLE `oil_well_reports` DISABLE KEYS */;
INSERT INTO `oil_well_reports` VALUES (38,70,'2025-07-18','3','1','2','','','','','','3','','','','','','','','','','','','','','','','','','','','','6.0','26.0','','','','','','','','5.0',''),(40,72,'2025-07-18','4','1','123','1','1','','','0','1','1','1','1','0','0','0','','','0','','','','','','','','','','','','369.0','147.0','','','','','','3.0','0','126.0','0.0'),(50,80,'2025-07-19','5','1','7','1','2','','','0','','0','0','0','0','8','0','','','0','','','','','','','9.0','','','','','24.0','32.0','','','','','','3.0','0','11.0','4.0'),(51,NULL,'2025-07-19','3','1','77','1','1','','是','1','','','','','','','','','','','','','','','','','7.0','','','','','18.0','30.0','','','','','','3.0','','9.0',''),(52,NULL,'2025-07-19','4','1','54','2','2','3','是','1','4','6','7','2','2','12','11','12','12','3','1','1','1','1','1','','7.0','','','','','15.0','29.0','','','','','','6.0','1','8.0','6.0'),(53,81,'2025-07-19','6','1','4','','','','','','','','','','','','','','','','','','','','','','','','','','','6.0','26.0','','','','','','','','5.0','');
/*!40000 ALTER TABLE `oil_well_reports` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `platformer`
--

DROP TABLE IF EXISTS `platformer`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `platformer` (
  `id` int NOT NULL AUTO_INCREMENT,
  `platformer_id` varchar(45) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `bao_id` varchar(45) COLLATE utf8mb4_general_ci NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=23 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `platformer`
--

LOCK TABLES `platformer` WRITE;
/*!40000 ALTER TABLE `platformer` DISABLE KEYS */;
INSERT INTO `platformer` VALUES (16,'1','29'),(20,'平台3','31');
/*!40000 ALTER TABLE `platformer` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `prod_team`
--

DROP TABLE IF EXISTS `prod_team`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `prod_team` (
  `team_id` int NOT NULL AUTO_INCREMENT,
  `area_id` int NOT NULL,
  `team_name` varchar(30) NOT NULL COMMENT '班组名称，如“注采八班”',
  `team_no` tinyint unsigned NOT NULL COMMENT '班组编号（1-n）',
  PRIMARY KEY (`team_id`),
  UNIQUE KEY `uk_area_teamNo` (`area_id`,`team_no`),
  CONSTRAINT `fk_team_area` FOREIGN KEY (`area_id`) REFERENCES `work_area` (`area_id`)
) ENGINE=InnoDB AUTO_INCREMENT=26 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='注采班';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `prod_team`
--

LOCK TABLES `prod_team` WRITE;
/*!40000 ALTER TABLE `prod_team` DISABLE KEYS */;
INSERT INTO `prod_team` VALUES (22,15,'采注1班',5),(24,16,'测试2班',0);
/*!40000 ALTER TABLE `prod_team` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `user_account`
--

DROP TABLE IF EXISTS `user_account`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `user_account` (
  `user_id` int NOT NULL AUTO_INCREMENT,
  `username` varchar(50) NOT NULL,
  `password` varchar(100) NOT NULL,
  `permission` varchar(50) NOT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`user_id`),
  UNIQUE KEY `username` (`username`)
) ENGINE=InnoDB AUTO_INCREMENT=24 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `user_account`
--

LOCK TABLES `user_account` WRITE;
/*!40000 ALTER TABLE `user_account` DISABLE KEYS */;
INSERT INTO `user_account` VALUES (9,'admin1','admin123','Admin','2025-05-20 15:29:45'),(22,'1','1','User2_作业一区_采注1班_110_油报','2025-07-18 03:51:39'),(23,'2','2','User1_作业一区_采注1班_110_水报','2025-07-18 03:51:47');
/*!40000 ALTER TABLE `user_account` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `well`
--

DROP TABLE IF EXISTS `well`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `well` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `room_id` int NOT NULL,
  `bao_id` varchar(45) NOT NULL,
  `platform_id` varchar(45) DEFAULT NULL,
  `well_code` varchar(30) NOT NULL COMMENT '井号，如“前60-11-13”',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_room_wellCode` (`room_id`,`well_code`),
  CONSTRAINT `fk_well_room` FOREIGN KEY (`room_id`) REFERENCES `meter_room` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=82 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='井基本信息';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `well`
--

LOCK TABLES `well` WRITE;
/*!40000 ALTER TABLE `well` DISABLE KEYS */;
INSERT INTO `well` VALUES (67,21,'28',NULL,'1'),(68,21,'28',NULL,'2'),(70,21,'29','16','3'),(72,21,'29','16','4'),(73,23,'30',NULL,'10'),(80,21,'29','16','5'),(81,21,'29','16','6');
/*!40000 ALTER TABLE `well` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `work_area`
--

DROP TABLE IF EXISTS `work_area`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `work_area` (
  `area_id` int NOT NULL AUTO_INCREMENT,
  `area_name` varchar(30) NOT NULL COMMENT '作业区，如“作业三区”',
  PRIMARY KEY (`area_id`),
  UNIQUE KEY `area_name` (`area_name`)
) ENGINE=InnoDB AUTO_INCREMENT=18 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='作业区';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `work_area`
--

LOCK TABLES `work_area` WRITE;
/*!40000 ALTER TABLE `work_area` DISABLE KEYS */;
INSERT INTO `work_area` VALUES (15,'作业一区'),(16,'测试2区');
/*!40000 ALTER TABLE `work_area` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2025-07-19 11:47:12
