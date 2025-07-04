-- MySQL dump 10.13  Distrib 8.0.40, for Win64 (x86_64)
--
-- Host: localhost    Database: water_report
-- ------------------------------------------------------
-- Server version	8.0.40

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
  CONSTRAINT `fk_report_well` FOREIGN KEY (`well_id`) REFERENCES `well` (`well_id`)
) ENGINE=InnoDB AUTO_INCREMENT=37 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='注水井日报';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `daily_report`
--

LOCK TABLES `daily_report` WRITE;
/*!40000 ALTER TABLE `daily_report` DISABLE KEYS */;
INSERT INTO `daily_report` VALUES (12,11,'2025-05-19','采注',0,0.0,0.0,0.0,0.0,0.00,0.00,'test1',0.00,0.00,0.00),(15,11,'2025-05-20','',0,0.0,0.0,0.0,0.0,0.00,0.00,'',0.00,0.00,0.00),(16,11,'2025-05-18','',0,0.0,0.0,0.0,0.0,0.00,0.00,'',0.00,0.00,0.00),(17,11,'2025-05-21','',0,0.0,0.0,0.0,0.0,0.00,0.00,'',0.00,0.00,0.00),(18,11,'2025-05-22','',0,0.0,0.0,0.0,0.0,0.00,0.00,'',0.00,0.00,0.00),(19,11,'2025-05-23','',0,0.0,0.0,0.0,0.0,0.00,0.00,'',0.00,0.00,0.00),(20,11,'2025-05-24','',0,0.0,0.0,0.0,0.0,0.00,0.00,'',0.00,0.00,0.00),(21,11,'2025-05-25','',0,0.0,0.0,0.0,0.0,0.00,0.00,'',0.00,0.00,0.00),(23,12,'2025-05-21','2',4,5.0,6.0,7.0,8.0,9.00,16.00,'17',10.00,12.00,14.00),(24,13,'2025-05-21','2',4,5.0,6.0,1.0,1.0,1.00,1.00,'1',1.00,1.00,1.00),(25,15,'2025-05-21','1',1,1.0,1.0,1.0,1.0,1.00,1.00,'1',1.00,1.00,1.00),(26,16,'2025-05-21','稳注',22,3.8,3.5,0.6,3.3,120.00,119.70,'自动入库示例2',40.10,39.80,39.80),(27,14,'2025-05-21','',0,0.0,0.0,0.0,0.0,0.00,0.00,'',1.00,2.00,3.00),(28,12,'2025-05-22','2',4,5.0,6.0,7.0,8.0,9.00,16.00,'5.22测试用',10.00,12.00,14.00),(29,14,'2025-05-22','',0,0.0,0.0,0.0,0.0,0.00,0.00,'',1.00,2.00,3.00),(30,15,'2025-05-22','1',1,1.0,1.0,1.0,1.0,1.00,1.00,'1',1.00,1.00,1.00),(31,16,'2025-05-22','稳注',22,3.8,3.5,0.6,3.3,120.00,119.70,'自动入库示例2',40.10,39.80,39.80),(32,20,'2025-05-23','注水2',0,0.0,0.0,0.0,0.0,0.00,0.00,'测试2',0.00,0.00,0.00),(33,12,'2025-05-23','2',4,5.0,6.0,7.0,8.0,9.00,16.00,'5.22测试用',15.00,12.00,14.00),(34,14,'2025-05-23','',0,0.0,0.0,0.0,0.0,0.00,0.00,'',1.00,2.00,3.00),(35,15,'2025-05-23','1',1,1.0,1.0,1.0,1.0,1.00,1.00,'1',1.00,1.00,1.00),(36,16,'2025-05-23','稳注',22,3.8,3.5,0.6,3.3,120.00,119.70,'自动入库示例2',40.10,39.80,39.80);
/*!40000 ALTER TABLE `daily_report` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `meter_room`
--

DROP TABLE IF EXISTS `meter_room`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `meter_room` (
  `room_id` int NOT NULL AUTO_INCREMENT,
  `team_id` int NOT NULL,
  `room_no` varchar(10) NOT NULL COMMENT '间号，如“104号”“ZS”',
  `is_injection_room` tinyint(1) DEFAULT '0' COMMENT '0=计量间 1=注水间',
  PRIMARY KEY (`room_id`),
  UNIQUE KEY `uk_team_roomNo` (`team_id`,`room_no`),
  CONSTRAINT `fk_room_team` FOREIGN KEY (`team_id`) REFERENCES `prod_team` (`team_id`)
) ENGINE=InnoDB AUTO_INCREMENT=11 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='计量间 / 注水间';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `meter_room`
--

LOCK TABLES `meter_room` WRITE;
/*!40000 ALTER TABLE `meter_room` DISABLE KEYS */;
INSERT INTO `meter_room` VALUES (5,4,'104号',0),(6,7,'108号',0),(8,10,'110号',0),(10,12,'104号',0);
/*!40000 ALTER TABLE `meter_room` ENABLE KEYS */;
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
) ENGINE=InnoDB AUTO_INCREMENT=13 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='注采班';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `prod_team`
--

LOCK TABLES `prod_team` WRITE;
/*!40000 ALTER TABLE `prod_team` DISABLE KEYS */;
INSERT INTO `prod_team` VALUES (4,4,'注采八班',8),(7,5,'注采二班',2),(8,5,'注采八班',8),(10,4,'注采七班',7),(11,5,'注采七班',7),(12,6,'注采8班',8);
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
) ENGINE=InnoDB AUTO_INCREMENT=14 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `user_account`
--

LOCK TABLES `user_account` WRITE;
/*!40000 ALTER TABLE `user_account` DISABLE KEYS */;
INSERT INTO `user_account` VALUES (7,'user1','user123','User_作业二区_注采八班_104号','2025-05-20 14:19:55'),(8,'advanced1','advance123','Advanced_作业二区_注采七班','2025-05-20 14:20:22'),(9,'admin1','admin123','Admin','2025-05-20 15:29:45'),(11,'DSB104','123456','User_作业一区_注采8班_104号','2025-05-23 06:36:43'),(12,'user2','123','User_作业三区_注采二班_108号','2025-05-23 06:52:52'),(13,'advance2','123','Advanced_作业二区_注采八班','2025-05-23 06:53:53');
/*!40000 ALTER TABLE `user_account` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `well`
--

DROP TABLE IF EXISTS `well`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `well` (
  `well_id` bigint NOT NULL AUTO_INCREMENT,
  `room_id` int NOT NULL,
  `well_code` varchar(30) NOT NULL COMMENT '井号，如“前60-11-13”',
  PRIMARY KEY (`well_id`),
  UNIQUE KEY `uk_room_wellCode` (`room_id`,`well_code`),
  CONSTRAINT `fk_well_room` FOREIGN KEY (`room_id`) REFERENCES `meter_room` (`room_id`)
) ENGINE=InnoDB AUTO_INCREMENT=21 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='井基本信息';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `well`
--

LOCK TABLES `well` WRITE;
/*!40000 ALTER TABLE `well` DISABLE KEYS */;
INSERT INTO `well` VALUES (12,5,'1'),(11,5,'103号'),(14,5,'2'),(15,5,'3'),(16,5,'前60-11-13'),(13,6,'1'),(17,6,'2'),(18,6,'3'),(20,10,'前60-11-13');
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
) ENGINE=InnoDB AUTO_INCREMENT=7 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='作业区';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `work_area`
--

LOCK TABLES `work_area` WRITE;
/*!40000 ALTER TABLE `work_area` DISABLE KEYS */;
INSERT INTO `work_area` VALUES (6,'作业一区'),(5,'作业三区'),(4,'作业二区');
/*!40000 ALTER TABLE `work_area` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Dumping events for database 'water_report'
--

--
-- Dumping routines for database 'water_report'
--
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2025-07-03 23:47:16
