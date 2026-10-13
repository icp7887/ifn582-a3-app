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
(1, 'Lara', 'scrypt:32768:8:1$UDRZD894ICUpo4Gt$0d841d454fdb36ebbbc19c627dbc3530d86f5130a94e5f1449f29536ee10d45bb6f6393b067f8a7d47e77ba973c58a920a15b4f1e3b77002a5521cf4a6b689b1', 'lara@email.com', '2027-01-01 00:00:00'),
(2, 'Jade', 'scrypt:32768:8:1$sq2erBkd0OrVF9tf$cf78f801d013e5e1c6c6f5964e68089a54d65b4ca2cdd8c749fdfc427084816f14fdfdd3f7aee9bca585a7e1ec99b295f5aed92b66013f6914af79143fb1bb95', 'jade@email.com', '2027-01-02 00:00:00'),
(3, 'Emma', 'scrypt:32768:8:1$ywkBTvxxYA37Jz3M$7d022aeb11bc44b3b88988c1941591bf4a3ae1e09c85e0a40734fb59edb1c6dc4c74fb9a0b68e7c6f27f81558a2cc01022254e6073178e5daa7e4d57f55e4fb6', 'emma@email.com', '2027-01-02 00:00:00'),
(4, 'Tessa', 'scrypt:32768:8:1$mNrufumEgW2Dn4ZQ$2ebf21477e785141c80853043fe4ca2dde2c6e4c4e6dcd2e507fb2c8a4d97bcc327539b0b08ee43cac8f4871c5582401addd65f2f3e87c757ecc812be358a844', 'tessa@email.com', '2027-01-03 00:00:00'),
(5, 'Maya', 'scrypt:32768:8:1$iGV3QOcSxLJ32cGF$520591deab4532661a5d4ea6846108296006300a2e0def07ac6477d008b56ea70ba0b068676c954d3fca08c2865e2caf8bb1786f4c465fb74a088aee22572eb5', 'maya@email.com', '2027-01-04 00:00:00'),
(6, 'Drake', 'scrypt:32768:8:1$2xmUgecvYPHANOb5$0a3a6a6be33dbca24eec111dade91eca444c2dc96f6fbf428e8c1eda8bc77a147540db64913244ac5ed5dbbf4523400bae2127f2808d340811b5087a60dfd22e', 'aubrey@ovo.com', '2027-01-07 00:00:00'),
(7, 'All-In', 'scrypt:32768:8:1$zD6ekamfkqMBmuSu$979351e43656ddf475372db7ce8c139c19b7b65f3b6648362c096378b320190c5cda72f485447f93675b7f71e1cd0a8c81b783995a21a91beed955892e8f1f81', 'chamath@allin.com', '2027-01-07 00:00:00'),
(8, 'MKBHD', 'scrypt:32768:8:1$hL3Z0DtEnswXNFHO$287ad3b419a993f7a291b5e2e85c6405a6ac9f8852e10b8e46693eaa347e9bc3183265be75f818c6cf016fb25fb584bfd83a1e474f020489d9ff86ed511029b3', 'mark@mkbhd.com', '2027-01-07 00:00:00'),
(9, 'MrBeast', 'scrypt:32768:8:1$nm7AwvCP8w5aVWC0$46413137046ab811ace29f21429c8124c8a316b244def9d18eb25fa5efd7a09f1f8c93f61e35e6ff51c5eefe4bb65d3b99d4dea7921414902ef5078b7fe95f98', 'jimmy@mrbeast.com', '2027-01-07 00:00:00'),
(10, 'Niko', 'scrypt:32768:8:1$u3QycqtjEoZB2tSe$b995ccd2da9955535f2c0339c3e7658469fe8c725c6c95b5f371cbef797a1c41e84d4a4c0d7a3481cd0d62dee9c925d2074c77b8a9749f1f9cc1dbdb0916269e', 'niko@betasquad.com', '2027-01-07 00:00:00'),
(11, 'Isaac', 'scrypt:32768:8:1$gGTR87oCaWahotTl$c283dc5b64704ac0c06491da51393f3a2ed52a8a72ccd780d52262d3f2b2cea6c358ab9762150c6554801bea708f70e000423cd93d7adfc90acb1cbecef3d81c', 'isaac@superchats.com', '2027-01-01 00:00:00'),
(12, 'Ido', 'scrypt:32768:8:1$6RkpNvTImvInXOos$28ada982df3d10555240cad7d4dc3575efb8ee4cd615fa75180a3e90c0bad778794c18890937a1146acc8a01e8c6170406d1f0618a5e1680df63d3dd10432f97', 'ido@superchats.com', '2027-01-01 00:00:00'),
(13, 'Daniel', 'scrypt:32768:8:1$Brn9K02qnFYkmpPF$f8c2123a965335528c784c569202ad04cde1adf38833524362c9012622f10c62a36879800c240805cbb9c744babae28459fe6b7c04b539f90f6f866a62ceb201', 'daniel@superchats.com', '2027-01-01 00:00:00'),
(14, 'Jacob', 'scrypt:32768:8:1$uQ6NkS9bReLgKcrP$417567c479b52c21e38fedd99852a7f0accbf563e91ba7caef53ba4243ef0207050adbed00a5d6ffc3915f6ff26d6901bad25f9244eb9bb58aa55c758f6c16f8', 'jacob@superchats.com', '2027-01-01 00:00:00'),
(15, 'Shem', 'scrypt:32768:8:1$8mARwCP81NM748Rf$87e0ba1826b5f9e44aaca688574c22c27918c97c30df885be7c0ef457a0734032416c95c6f2e884a26ee1ed7971d15748037aca8d97448cb137fca7595b0ae38', 'shem@superchats.com', '2027-01-01 00:00:00');


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