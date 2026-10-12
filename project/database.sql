# ============================================================
# SUPERCHAT DATABASE
# ============================================================

DROP DATABASE IF EXISTS superchat;
CREATE DATABASE superchat;
USE superchat;


# ============================================================
# DDL - TABLES
# ============================================================

# ------------------------------------------------------------
# User
# ------------------------------------------------------------

CREATE TABLE user (
    id INT NOT NULL AUTO_INCREMENT,
    username VARCHAR(50) NOT NULL UNIQUE,
    passwordHASH VARCHAR(250) NOT NULL,
    email VARCHAR(100) NOT NULL UNIQUE,
    dateJoined DATETIME DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id)
);


# ------------------------------------------------------------
# Creator
# ------------------------------------------------------------

CREATE TABLE creator (
    id INT NOT NULL,
    bio TEXT,
    totalEarnings DECIMAL(10,2) DEFAULT 0.00,
    verifiedStatus BOOLEAN DEFAULT TRUE,
    PRIMARY KEY (id),
    FOREIGN KEY (id)
        REFERENCES user(id)
        ON DELETE CASCADE
        ON UPDATE CASCADE
);


# ------------------------------------------------------------
# Admin
# ------------------------------------------------------------

CREATE TABLE admin (
    id INT NOT NULL,
    accessLevel VARCHAR(50) NOT NULL DEFAULT 'Admin',
    PRIMARY KEY (id),
    FOREIGN KEY (id)
        REFERENCES user(id)
        ON DELETE CASCADE
        ON UPDATE CASCADE
);


# ------------------------------------------------------------
# Subscription Tier
# ------------------------------------------------------------

CREATE TABLE subscriptionTier (
    id INT NOT NULL AUTO_INCREMENT,
    tierName VARCHAR(50) NOT NULL,
    price DECIMAL(10,2) DEFAULT 0.00,
    description TEXT,
    creatorID INT NOT NULL,
    PRIMARY KEY (id),
    FOREIGN KEY (creatorID)
        REFERENCES creator(id)
        ON DELETE CASCADE
        ON UPDATE CASCADE
);


# ------------------------------------------------------------
# Customer
# ------------------------------------------------------------

CREATE TABLE customer (
    id INT NOT NULL,
    paymentMethod VARCHAR(100),
    dateSubscribed DATETIME DEFAULT CURRENT_TIMESTAMP,
    subscribedTierID INT,
    PRIMARY KEY (id),
    FOREIGN KEY (id)
        REFERENCES user(id)
        ON DELETE CASCADE
        ON UPDATE CASCADE,
    FOREIGN KEY (subscribedTierID)
        REFERENCES subscriptionTier(id)
        ON DELETE SET NULL
        ON UPDATE CASCADE
);


# ------------------------------------------------------------
# Campaign
# ------------------------------------------------------------

CREATE TABLE campaign (
    id INT NOT NULL AUTO_INCREMENT,
    title VARCHAR(150) NOT NULL,
    goalAmount DECIMAL(10,2) DEFAULT 0.00,
    status VARCHAR(30) NOT NULL DEFAULT 'Pending',
    campaignImage VARCHAR(255),
    startDate DATE NOT NULL,
    endDate DATE NOT NULL,
    isFeatured BOOLEAN DEFAULT FALSE,
    isFlagged BOOLEAN DEFAULT FALSE,
    creatorID INT NOT NULL,
    category VARCHAR(50) NOT NULL,
    PRIMARY KEY (id),
    FOREIGN KEY (creatorID)
        REFERENCES creator(id)
        ON DELETE CASCADE
        ON UPDATE CASCADE
);


# ------------------------------------------------------------
# Donation
# ------------------------------------------------------------

CREATE TABLE donation (
    transactionID INT NOT NULL AUTO_INCREMENT,
    amount DECIMAL(10,2) DEFAULT 0.00,
    paymentNetwork VARCHAR(50) NOT NULL,
    transactionDate DATETIME DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(50) NOT NULL DEFAULT 'Pending',
    customerID INT NOT NULL,
    campaignID INT NOT NULL,
    PRIMARY KEY (transactionID),
    FOREIGN KEY (customerID)
        REFERENCES customer(id)
        ON DELETE CASCADE
        ON UPDATE CASCADE,
    FOREIGN KEY (campaignID)
        REFERENCES campaign(id)
        ON DELETE CASCADE
        ON UPDATE CASCADE
);


# ------------------------------------------------------------
# Campaign Post
# ------------------------------------------------------------

CREATE TABLE campaign_post (
    id INT NOT NULL AUTO_INCREMENT,
    campaignID INT NOT NULL,
    title VARCHAR(150) NOT NULL,
    content TEXT NOT NULL,
    postDate DATE NOT NULL,
    PRIMARY KEY (id),
    FOREIGN KEY (campaignID)
        REFERENCES campaign(id)
        ON DELETE CASCADE
        ON UPDATE CASCADE
);


# ============================================================
# DML - SAMPLE DATA
# ============================================================

# ------------------------------------------------------------
# Users
# ------------------------------------------------------------

INSERT INTO user
(id, username, passwordHASH, email, dateJoined)
VALUES
(1, 'Lara', '$2b$12$K9...', 'lara@email.com', '2027-01-01 00:00:00'),
(2, 'Jade', '$2b$12$R7...', 'jade@email.com', '2027-01-02 00:00:00'),
(3, 'Emma', '$2b$12$P2...', 'emma@email.com', '2027-01-02 00:00:00'),
(4, 'Tessa', '$2b$12$Y1...', 'tessa@email.com', '2027-01-03 00:00:00'),
(5, 'Maya', '$2b$12$X5...', 'maya@email.com', '2027-01-04 00:00:00'),
(6, 'Drake', '$2b$12$L2...', 'aubrey@ovo.com', '2027-01-07 00:00:00'),
(7, 'All-In', '$2b$12$Z2...', 'chamath@allin.com', '2027-01-07 00:00:00'),
(8, 'MKBHD', '$2b$12$L2...', 'mark@mkbhd.com', '2027-01-07 00:00:00'),
(9, 'MrBeast', '$2b$13$L2...', 'jimmy@mrbeast.com', '2027-01-07 00:00:00'),
(10, 'Niko', '$2b$07$Z2...', 'niko@betasquad.com', '2027-01-07 00:00:00'),
(11, 'Isaac', '$2b$12$L2...', 'isaac@superchats.com', '2027-01-01 00:00:00'),
(12, 'Ido', '$2b$12$L2...', 'ido@superchats.com', '2027-01-01 00:00:00'),
(13, 'Daniel', '$2b$12$L2...', 'daniel@superchats.com', '2027-01-01 00:00:00'),
(14, 'Jacob', '$2b$12$L2...', 'jacob@superchats.com', '2027-01-01 00:00:00'),
(15, 'Shem', '$2b$12$L2...', 'shem@superchats.com', '2027-01-01 00:00:00');


# ------------------------------------------------------------
# Creators
# ------------------------------------------------------------

INSERT INTO creator
(id, bio, totalEarnings, verifiedStatus)
VALUES
(6, 'Album cover art', 2600.00, TRUE),
(7, 'All-in Summit', 3000.00, TRUE),
(8, '4K Camera', 0.00, FALSE),
(9, 'YouTube Video', 0.00, FALSE),
(10, 'Water Project', 0.00, FALSE);


# ------------------------------------------------------------
# Admins
# ------------------------------------------------------------

INSERT INTO admin
(id, accessLevel)
VALUES
(11, 'Super-Admin'),
(12, 'Admin'),
(13, 'Admin'),
(14, 'Admin'),
(15, 'Admin');


# ------------------------------------------------------------
# Subscription Tiers
# ------------------------------------------------------------

INSERT INTO subscriptionTier
(id, tierName, price, description, creatorID)
VALUES
(1, 'Stan', 5.00, 'Join WhatsApp group', 6),
(2, 'Member', 15.00, 'Behind the scenes content', 6),
(3, 'Superfan', 30.00, 'Facetime call', 6),
(4, 'Member', 15.00, 'Follow back on IG', 7),
(5, 'Superfan', 30.00, 'Free merch', 7);


# ------------------------------------------------------------
# Customers
# ------------------------------------------------------------

INSERT INTO customer
(id, paymentMethod, dateSubscribed, subscribedTierID)
VALUES
(1, 'Mastercard', '2027-01-01 00:00:00', 1),
(2, 'Visa', '2027-01-02 00:00:00', 2),
(3, 'Mastercard', '2027-01-02 00:00:00', 3),
(4, 'Visa', '2027-01-03 00:00:00', 4),
(5, 'Mastercard', '2027-01-04 00:00:00', 4);


# ------------------------------------------------------------
# Campaigns
# ------------------------------------------------------------

INSERT INTO campaign
(id, title, goalAmount, status, campaignImage,
 startDate, endDate, isFeatured, isFlagged, creatorID, category)
VALUES
(1, 'Water Project', 10000.00, 'Active', 'charity.png',
 '2027-01-07', '2027-02-07', TRUE, FALSE, 10, 'Community'),

(2, 'Music Album', 50000.00, 'Active', 'music-album.png',
 '2027-01-07', '2027-02-07', TRUE, FALSE, 6, 'Arts'),

(3, 'All-in Summit', 500.00, 'Pending', 'banner.png',
 '2027-01-07', '2027-02-07', TRUE, FALSE, 7, 'Technology'),

(4, 'VR Glasses', 3000.00, 'Pending', 'vr.png',
 '2027-01-07', '2027-02-07', FALSE, FALSE, 8, 'Technology'),

(5, 'India Fund', 2000.00, 'Pending', 'india.png',
 '2027-01-07', '2027-02-07', FALSE, TRUE, 9, 'Community'),

(6, 'School Supplies Drive', 7500.00, 'Active', 'school.png',
 '2027-01-08', '2027-02-08', FALSE, FALSE, 6, 'Education'),

(7, 'Community Food Relief', 12000.00, 'Active', 'food.png',
 '2027-01-08', '2027-02-08', FALSE, FALSE, 7, 'Community'),

(8, 'Rural Education Fund', 8500.00, 'Active', 'education.png',
 '2027-01-09', '2027-02-09', FALSE, FALSE, 8, 'Education'),

(9, 'Youth Sports Program', 9000.00, 'Active', 'sports.png',
 '2027-01-09', '2027-02-09', FALSE, FALSE, 9, 'Community'),

(10, 'Clean Water Initiative', 15000.00, 'Active', 'water.png',
 '2027-01-10', '2027-02-10', FALSE, FALSE, 10, 'Community'),

(11, 'Local Arts Festival', 6000.00, 'Active', 'arts.png',
 '2027-01-10', '2027-02-10', FALSE, FALSE, 6, 'Arts'),

(12, 'Medical Support Fund', 13000.00, 'Active', 'medical.png',
 '2027-01-11', '2027-02-11', FALSE, FALSE, 7, 'Health'),

(13, 'Digital Learning Project', 11000.00, 'Active', 'digital.png',
 '2027-01-11', '2027-02-11', FALSE, FALSE, 8, 'Technology'),

(14, 'Community Garden', 6500.00, 'Active', 'garden.png',
 '2027-01-12', '2027-02-12', FALSE, FALSE, 9, 'Community'),

(15, 'Emergency Relief Fund', 10000.00, 'Active', 'emergency.png',
 '2027-01-12', '2027-02-12', FALSE, FALSE, 10, 'Community');


# ------------------------------------------------------------
# Donations
# ------------------------------------------------------------

INSERT INTO donation
(transactionID, amount, paymentNetwork, transactionDate,
 status, customerID, campaignID)
VALUES
(1, 26.00, 'Mastercard', '2027-01-01 00:00:00', 'Done', 1, 1),
(2, 26.00, 'Visa', '2027-01-02 00:00:00', 'Done', 2, 2),
(3, 26.00, 'Mastercard', '2027-01-02 00:00:00', 'Done', 3, 3),
(4, 26.00, 'Visa', '2027-01-03 00:00:00', 'Done', 4, 1),
(5, 26.00, 'Mastercard', '2027-01-04 00:00:00', 'Done', 5, 2);


# ------------------------------------------------------------
# Campaign Posts
# ------------------------------------------------------------

INSERT INTO campaign_post
(id, campaignID, title, content, postDate)
VALUES
(1, 1, 'Water Project Update',
 'We have started work on the water project and preparations are underway.',
 '2027-01-15'),

(2, 2, 'Music Album Progress',
 'Recording for the new music album is currently underway.',
 '2027-01-16'),

(3, 3, 'All-in Summit Update',
 'Planning and preparation for the All-in Summit have begun.',
 '2027-01-17');