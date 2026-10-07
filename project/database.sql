#DDL Queries
drop database if exists superchat;
create database superchat;
use superchat;

#user table
create table user(
	id INT NOT NULL auto_increment,
    username VARCHAR(50) NOT NULL UNIQUE,
    passwordHASH VARCHAR(250) NOT NULL,
    email VARCHAR(100) NOT NULL UNIQUE,
    dateJoined DATETIME DEFAULT current_timestamp,
    primary key (id)
);

#creator, and admin
Create table creator(
	id int not null, #id does not need auto_increment since it's a foreign key for user table
    bio TEXT,
    totalEarnings decimal(10,2) Default 0.00,
    verifiedStatus Boolean default True,
    primary key(id),
    foreign key(id) references user(id) on delete cascade on update cascade #primary key references are orignially not null, so it will conflict if we delete a row and it's set to NULL
);

Create table admin(
	id int not null, #id does not need auto_increment since it's a foreign key for user table
    accessLevel varchar(50) not null default 'Admin',
    primary key(id),
    foreign key(id) references user(id) on delete cascade on update cascade
);

#creating main tables - subscriptionTier, campaign, donation, campaign_post
create table subscriptionTier(
	id int not null auto_increment,
    tierName varchar(50) not null,
    price decimal(10,2) default 0.00,
    description TEXT,
    creatorID int not null,
    primary key(id),
    foreign key(creatorID) references creator(id) on delete cascade on update cascade 
);


create table customer(
	id INT NOT NULL,  #id does not need auto_increment since it's a foreign key for user table
    paymentMethod VARCHAR (100),
    dateSubscribed DATETIME DEFAULT current_timestamp,
    subscribedTierID INT, #not null not necessary since a user does not need to pay for a subscription upon creation
    primary key(id),
    foreign key(id) references user(id) on delete cascade on update cascade, 
    foreign key(subscribedTierID) references subscriptionTier(id) on delete set null on update cascade #SET NULL prevents deleting customers when tiers are removed
);

create table campaign(
	id int auto_increment primary key,
    title varchar(150) not null,
    goalAmount decimal(10,2) default 0.00,
    status varchar(30) not null default 'pending',
    campaignImage varchar(255),
    startDate DATE NOT NULL,
    endDate DATE NOT NULL,
    isFeatured Boolean default false,
    isFlagged Boolean default false,
    creatorID int not null,
    category varchar(50) not null,
    foreign key(creatorID) references creator(id) on delete cascade on update cascade
);

create table donation(
	transactionID int not null auto_increment,
    amount decimal(10,2) default 0.00,
    paymentNetwork varchar(50) not null,
    transactionDate DATETIME default current_timestamp,
    status varchar(50) not null default 'Pending',
    customerID int not null,
    campaignID int not null,
    primary key(transactionID),
    foreign key(customerID) references customer(id) on delete cascade on update cascade, 
    foreign key(campaignID) references campaign(id) on delete cascade on update cascade 
);

create table campaign_post(
	id int primary key auto_increment,
    campaignID int not null,
    title varchar(150) not null,
    content TEXT not null,
    postDate DATE NOT NULL,
    foreign key(campaignID) references campaign(id) on delete cascade on update cascade
);

#DML Queries
INSERT INTO user (id, username, passwordHASH, email, dateJoined) VALUES
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
    
INSERT INTO creator (id, bio, totalEarnings, verifiedStatus) VALUES
	(6, 'Album cover art', 2600.00, TRUE),
	(7, 'All-in Summit', 3000.00, TRUE),
	(8, '4K Camera', 0.00, FALSE),
	(9, 'YouTube Video', 0.00, FALSE),
	(10, 'Water Project', 0.00, FALSE);
    
INSERT INTO admin (id, accessLevel) VALUES
	(11, 'Super-Admin'),
	(12, 'Admin'),
	(13, 'Admin'),
	(14, 'Admin'),
	(15, 'Admin');
    
INSERT INTO subscriptionTier (id, tierName, price, description, creatorID) VALUES
	(1, 'Stan', 5.00, 'Join WhatsApp group', 6),
	(2, 'Member', 15.00, 'Behind the scenes content', 6),
	(3, 'Superfan', 30.00, 'Facetime call', 6),
	(4, 'Member', 15.00, 'Follow back on IG', 7),
	(5, 'Superfan', 30.00, 'Free merch', 7);
    
INSERT INTO customer (id, paymentMethod, dateSubscribed, subscribedTierID) VALUES
	(1, 'Mastercard', '2027-01-01 00:00:00', 1),
	(2, 'Visa', '2027-01-02 00:00:00', 2),
	(3, 'Mastercard', '2027-01-02 00:00:00', 3),
	(4, 'Visa', '2027-01-03 00:00:00', 4),
	(5, 'Mastercard', '2027-01-04 00:00:00', 4);
    
INSERT INTO campaign (id, title, goalAmount, status, campaignImage, startDate, endDate, isFeatured, isFlagged, creatorID, category) VALUES
	(1, 'Water Project', 10000.00, 'Active', 'charity.png', '2027-01-07 00:00:00', '2027-02-07 00:00:00', TRUE, FALSE, 10, 'Community'),
	(2, 'Music Album', 50000.00, 'Active', 'music-album.png', '2027-01-07 00:00:00', '2027-02-07 00:00:00', TRUE, FALSE, 6, 'Arts'),
	(3, 'All-in Summit', 500.00, 'Pending', 'banner.png', '2027-01-07 00:00:00', '2027-02-07 00:00:00', TRUE, FALSE, 7, 'Technology'),
	(4, 'VR Glasses', 3000.00, 'Pending', 'vr.png', '2027-01-07 00:00:00', '2027-02-07 00:00:00', FALSE, FALSE, 8, 'Technology'),
	(5, 'India Fund', 2000.00, 'Pending', 'india.png', '2027-01-07 00:00:00', '2027-02-07 00:00:00', FALSE, TRUE, 9, 'Community'),
	(6, 'School Supplies Drive', 7500.00, 'Active', 'school.png', '2027-01-08 00:00:00', '2027-02-08 00:00:00', FALSE, FALSE, 6, 'Education'),
	(7, 'Community Food Relief', 12000.00, 'Active', 'food.png', '2027-01-08 00:00:00', '2027-02-08 00:00:00', FALSE, FALSE, 7, 'Community'),
	(8, 'Rural Education Fund', 8500.00, 'Active', 'education.png', '2027-01-09 00:00:00', '2027-02-09 00:00:00', FALSE, FALSE, 8, 'Education'),
	(9, 'Youth Sports Program', 9000.00, 'Active', 'sports.png', '2027-01-09 00:00:00', '2027-02-09 00:00:00', FALSE, FALSE, 9, 'Community'),
	(10, 'Clean Water Initiative', 15000.00, 'Active', 'water.png', '2027-01-10 00:00:00', '2027-02-10 00:00:00', FALSE, FALSE, 10, 'Community'),
	(11, 'Local Arts Festival', 6000.00, 'Active', 'arts.png', '2027-01-10 00:00:00', '2027-02-10 00:00:00', FALSE, FALSE, 6, 'Arts'),
	(12, 'Medical Support Fund', 13000.00, 'Active', 'medical.png', '2027-01-11 00:00:00', '2027-02-11 00:00:00', FALSE, FALSE, 7, 'Health'),
	(13, 'Digital Learning Project', 11000.00, 'Active', 'digital.png', '2027-01-11 00:00:00', '2027-02-11 00:00:00', FALSE, FALSE, 8, 'Technology'),
	(14, 'Community Garden', 6500.00, 'Active', 'garden.png', '2027-01-12 00:00:00', '2027-02-12 00:00:00', FALSE, FALSE, 9, 'Community'),
	(15, 'Emergency Relief Fund', 10000.00, 'Active', 'emergency.png', '2027-01-12 00:00:00', '2027-02-12 00:00:00', FALSE, FALSE, 10, 'Community');
    
INSERT INTO donation (transactionID, amount, paymentNetwork, transactionDate, status, customerID, campaignID) VALUES
	(1, 26.00, 'Mastercard', '2027-01-01 00:00:00', 'Done', 1, 1),
	(2, 26.00, 'Visa', '2027-01-02 00:00:00', 'Done', 2, 2),
	(3, 26.00, 'Mastercard', '2027-01-02 00:00:00', 'Done', 3, 3),
	(4, 26.00, 'Visa', '2027-01-03 00:00:00', 'Done', 4, 1),
	(5, 26.00, 'Mastercard', '2027-01-04 00:00:00', 'Done', 5, 2);
    
INSERT INTO campaign_post (id, campaignID, title, content, postDate) VALUES
	(1, 1, 'Water Project Update', 'We have started work on the water project and preparations are underway.', '2027-01-15 00:00:00'),
	(2, 2, 'Music Album Progress', 'Recording for the new music album is currently underway.', '2027-01-16 00:00:00'),
	(3, 3, 'All-in Summit Update', 'Planning and preparation for the All-in Summit have begun.', '2027-01-17 00:00:00');
    
UPDATE user SET passwordHASH = 'adminpassword123' WHERE id = 12;

ALTER TABLE user CHANGE COLUMN passwordHASH password VARCHAR(250);

UPDATE user SET password = 'lara123' WHERE id = 1;
UPDATE user SET password = 'jade123' WHERE id = 2;
UPDATE user SET password = 'emma123' WHERE id = 3;
UPDATE user SET password = 'tessa123' WHERE id = 4;
UPDATE user SET password = 'maya123' WHERE id = 5;
UPDATE user SET password = 'drake123' WHERE id = 6;
UPDATE user SET password = 'allin123' WHERE id = 7;
UPDATE user SET password = 'mkbhd123' WHERE id = 8;
UPDATE user SET password = 'mrbeast123' WHERE id = 9;
UPDATE user SET password = 'niko123' WHERE id = 10;
UPDATE user SET password = 'isaac123' WHERE id = 11;
UPDATE user SET password = 'daniel123' WHERE id = 13;
UPDATE user SET password = 'jacob123' WHERE id = 14;
UPDATE user SET password = 'shem123' WHERE id = 15;