-- phpMyAdmin SQL Dump
-- version 5.2.1
-- https://www.phpmyadmin.net/
--
-- Host: 127.0.0.1
-- Generation Time: Jul 21, 2025 at 11:23 AM
-- Server version: 10.4.32-MariaDB
-- PHP Version: 8.2.12

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Database: `project_bin`
--

-- --------------------------------------------------------

--
-- Table structure for table `session`
--

CREATE TABLE `session` (
  `id` int(11) NOT NULL,
  `order_id` varchar(50) NOT NULL,
  `products_id` varchar(50) DEFAULT NULL,
  `products_name` varchar(100) DEFAULT NULL,
  `barcode_id` varchar(50) DEFAULT NULL,
  `quantity` int(11) DEFAULT 1,
  `disquantity` int(11) DEFAULT 0,
  `email` varchar(100) DEFAULT NULL,
  `order_date` timestamp NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `tbl_category`
--

CREATE TABLE `tbl_category` (
  `id` int(11) NOT NULL,
  `category_id` varchar(50) NOT NULL,
  `category_name` varchar(100) NOT NULL,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `tbl_category`
--

INSERT INTO `tbl_category` (`id`, `category_id`, `category_name`, `created_at`) VALUES
(1, 'CAT001', 'Electronics', '2025-07-20 06:41:27'),
(2, 'CAT002', 'Clothing', '2025-07-20 06:41:27'),
(3, 'CAT003', 'Books', '2025-07-20 06:41:27'),
(4, 'CAT004', 'Food & Beverages', '2025-07-20 06:41:27'),
(5, '1', 'Home & Garden', '2025-07-20 06:41:27');

-- --------------------------------------------------------

--
-- Table structure for table `tbl_order`
--

CREATE TABLE `tbl_order` (
  `id` int(11) NOT NULL,
  `order_id` varchar(50) NOT NULL,
  `products_id` varchar(50) DEFAULT NULL,
  `products_name` varchar(100) DEFAULT NULL,
  `barcode_id` varchar(50) DEFAULT NULL,
  `quantity` int(11) DEFAULT 1,
  `disquantity` int(11) DEFAULT 0,
  `email` varchar(100) DEFAULT NULL,
  `order_date` timestamp NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `tbl_order`
--

INSERT INTO `tbl_order` (`id`, `order_id`, `products_id`, `products_name`, `barcode_id`, `quantity`, `disquantity`, `email`, `order_date`) VALUES
(13, '101', '1234567891234', 'แป๊ปซี่', '9568046394532', 1, 0, 'pianlerdpringpror@gmail.com', '2025-07-21 08:52:36'),
(14, '101', '1234567890123', 'Organic Coffee', '0749107154764', 1, 0, 'pianlerdpringpror@gmail.com', '2025-07-21 08:53:40'),
(15, '102', '1234567890123', 'Organic Coffee', '0301768063239', 1, 0, 'pianlerdpringpror@gmail.com', '2025-07-21 08:58:18'),
(16, '103', '1234567891234', 'แป๊ปซี่', '9541666998174', 3, 0, 'pianlerdpringpror@gmail.com', '2025-07-21 08:59:22'),
(17, '103', '1234567890123', 'Organic Coffee', '9541666998174', 1, 0, 'pianlerdpringpror@gmail.com', '2025-07-21 08:59:53'),
(18, '104', '1234567890123', 'Organic Coffee', '9968405968705', 3, 0, 'pianlerdpringpror@gmail.com', '2025-07-21 09:00:28'),
(19, '104', '1234567891234', 'แป๊ปซี่', '9968405968705', 1, 0, 'pianlerdpringpror@gmail.com', '2025-07-21 09:01:22'),
(20, '105', '1234567890123', 'Organic Coffee', '3534704382645', 1, 0, 'pianlerdpringpror@gmail.com', '2025-07-21 09:02:45'),
(21, '105', '1234567891234', 'แป๊ปซี่', '3534704382645', 1, 0, 'pianlerdpringpror@gmail.com', '2025-07-21 09:02:47'),
(22, '106', '1234567890123', 'Organic Coffee', '5483439457599', 1, 0, 'pianlerdpringpror@gmail.com', '2025-07-21 09:11:04');

-- --------------------------------------------------------

--
-- Table structure for table `tbl_products`
--

CREATE TABLE `tbl_products` (
  `id` int(11) NOT NULL,
  `products_id` varchar(50) NOT NULL,
  `products_name` varchar(100) NOT NULL,
  `stock` int(11) DEFAULT 0,
  `price` decimal(10,2) DEFAULT 0.00,
  `category_id` varchar(50) DEFAULT NULL,
  `description` text DEFAULT NULL,
  `barcode_id` varchar(50) DEFAULT NULL,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `tbl_products`
--

INSERT INTO `tbl_products` (`id`, `products_id`, `products_name`, `stock`, `price`, `category_id`, `description`, `barcode_id`, `created_at`) VALUES
(5, '1234567890123', 'Organic Coffee', 67, 350.00, '1', 'Premium organic coffee beans', 'BC005', '2025-07-20 06:41:27'),
(6, '1234567891234', 'แป๊ปซี่', 894, 1000.00, 'CAT003', '1233456', NULL, '2025-07-21 08:52:20');

-- --------------------------------------------------------

--
-- Table structure for table `tbl_users`
--

CREATE TABLE `tbl_users` (
  `id` int(11) NOT NULL,
  `firstname` varchar(100) NOT NULL,
  `lastname` varchar(100) NOT NULL,
  `email` varchar(100) NOT NULL,
  `password` varchar(255) NOT NULL,
  `role` enum('root_admin','administrator','moderator','member','viewer') DEFAULT 'member',
  `created_at` timestamp NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `tbl_users`
--

INSERT INTO `tbl_users` (`id`, `firstname`, `lastname`, `email`, `password`, `role`, `created_at`) VALUES
(1, 'Pianlerd', 'Pringpror', 'pianlerdpringpror@gmail.com', '123456', 'root_admin', '2025-07-20 06:41:27'),
(2, 'John', 'Manager', 'manager@example.com', 'manager123', 'administrator', '2025-07-20 06:41:27'),
(3, 'Jane', 'Moderator', 'moderator@example.com', 'moderator123', 'moderator', '2025-07-20 06:41:27'),
(4, 'Mike', 'Member', 'member@example.com', 'member123', 'member', '2025-07-20 06:41:27'),
(6, 'Pianlerd', 'Pringpror', 'pianlerdprigpror@gmail.com', '123456', 'member', '2025-07-21 06:44:03');

--
-- Indexes for dumped tables
--

--
-- Indexes for table `session`
--
ALTER TABLE `session`
  ADD PRIMARY KEY (`id`),
  ADD KEY `products_id` (`products_id`),
  ADD KEY `email` (`email`);

--
-- Indexes for table `tbl_category`
--
ALTER TABLE `tbl_category`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `category_id` (`category_id`);

--
-- Indexes for table `tbl_order`
--
ALTER TABLE `tbl_order`
  ADD PRIMARY KEY (`id`),
  ADD KEY `products_id` (`products_id`),
  ADD KEY `email` (`email`);

--
-- Indexes for table `tbl_products`
--
ALTER TABLE `tbl_products`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `products_id` (`products_id`),
  ADD KEY `category_id` (`category_id`);

--
-- Indexes for table `tbl_users`
--
ALTER TABLE `tbl_users`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `email` (`email`);

--
-- AUTO_INCREMENT for dumped tables
--

--
-- AUTO_INCREMENT for table `session`
--
ALTER TABLE `session`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `tbl_category`
--
ALTER TABLE `tbl_category`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=6;

--
-- AUTO_INCREMENT for table `tbl_order`
--
ALTER TABLE `tbl_order`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=23;

--
-- AUTO_INCREMENT for table `tbl_products`
--
ALTER TABLE `tbl_products`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=7;

--
-- AUTO_INCREMENT for table `tbl_users`
--
ALTER TABLE `tbl_users`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=7;

--
-- Constraints for dumped tables
--

--
-- Constraints for table `session`
--
ALTER TABLE `session`
  ADD CONSTRAINT `session_ibfk_1` FOREIGN KEY (`products_id`) REFERENCES `tbl_products` (`products_id`) ON DELETE CASCADE,
  ADD CONSTRAINT `session_ibfk_2` FOREIGN KEY (`email`) REFERENCES `tbl_users` (`email`) ON DELETE CASCADE;

--
-- Constraints for table `tbl_order`
--
ALTER TABLE `tbl_order`
  ADD CONSTRAINT `tbl_order_ibfk_1` FOREIGN KEY (`products_id`) REFERENCES `tbl_products` (`products_id`) ON DELETE CASCADE,
  ADD CONSTRAINT `tbl_order_ibfk_2` FOREIGN KEY (`email`) REFERENCES `tbl_users` (`email`) ON DELETE CASCADE;

--
-- Constraints for table `tbl_products`
--
ALTER TABLE `tbl_products`
  ADD CONSTRAINT `tbl_products_ibfk_1` FOREIGN KEY (`category_id`) REFERENCES `tbl_category` (`category_id`) ON DELETE SET NULL;
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
