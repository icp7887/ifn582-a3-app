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
	(12, 'admin', '$2b$12$L2...', 'ido@superchats.com', '2027-01-01 00:00:00'),
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
	(1, 'Water Project', 10000.00, 'Active', 'https://images.unsplash.com/photo-1538300342682-cf57afb97285?w=800&q=70&auto=format&fit=crop', '2027-01-07 00:00:00', '2027-02-07 00:00:00', TRUE, FALSE, 10, 'Community'),
	(2, 'Music Album', 50000.00, 'Active', 'https://images.unsplash.com/photo-1511379938547-c1f69419868d?w=800&q=70&auto=format&fit=crop', '2027-01-07 00:00:00', '2027-02-07 00:00:00', TRUE, FALSE, 6, 'Arts'),
	(3, 'All-in Summit', 500.00, 'Pending', 'https://images.unsplash.com/photo-1540575467063-178a50c2df87?w=800&q=70&auto=format&fit=crop', '2027-01-07 00:00:00', '2027-02-07 00:00:00', TRUE, FALSE, 7, 'Technology'),
	(4, 'VR Glasses', 3000.00, 'Pending', 'https://images.unsplash.com/photo-1593508512255-86ab42a8e620?w=800&q=70&auto=format&fit=crop', '2027-01-07 00:00:00', '2027-02-07 00:00:00', FALSE, FALSE, 8, 'Technology'),
	(5, 'India Fund', 2000.00, 'Pending', 'https://images.unsplash.com/photo-1524492412937-b28074a5d7da?w=800&q=70&auto=format&fit=crop', '2027-01-07 00:00:00', '2027-02-07 00:00:00', FALSE, TRUE, 9, 'Community'),
	(6, 'School Supplies Drive', 7500.00, 'Active', 'https://images.unsplash.com/photo-1503676260728-1c00da094a0b?w=800&q=70&auto=format&fit=crop', '2027-01-08 00:00:00', '2027-02-08 00:00:00', FALSE, FALSE, 6, 'Education'),
	(7, 'Community Food Relief', 12000.00, 'Active', 'https://images.unsplash.com/photo-1488521787991-ed7bbaae773c?w=800&q=70&auto=format&fit=crop', '2027-01-08 00:00:00', '2027-02-08 00:00:00', FALSE, FALSE, 7, 'Community'),
	(8, 'Rural Education Fund', 8500.00, 'Active', 'https://images.unsplash.com/photo-1497633762265-9d179a990aa6?w=800&q=70&auto=format&fit=crop', '2027-01-09 00:00:00', '2027-02-09 00:00:00', FALSE, FALSE, 8, 'Education'),
	(9, 'Youth Sports Program', 9000.00, 'Active', 'https://images.unsplash.com/photo-1461896836934-ffe607ba8211?w=800&q=70&auto=format&fit=crop', '2027-01-09 00:00:00', '2027-02-09 00:00:00', FALSE, FALSE, 9, 'Community'),
	(10, 'Clean Water Initiative', 15000.00, 'Active', 'https://images.unsplash.com/photo-1548839140-29a749e1cf4d?w=800&q=70&auto=format&fit=crop', '2027-01-10 00:00:00', '2027-02-10 00:00:00', FALSE, FALSE, 10, 'Community'),
	(11, 'Local Arts Festival', 6000.00, 'Active', 'https://images.unsplash.com/photo-1460661419201-fd4cecdf8a8b?w=800&q=70&auto=format&fit=crop', '2027-01-10 00:00:00', '2027-02-10 00:00:00', FALSE, FALSE, 6, 'Arts'),
	(12, 'Medical Support Fund', 13000.00, 'Active', 'https://images.unsplash.com/photo-1576091160399-112ba8d25d1d?w=800&q=70&auto=format&fit=crop', '2027-01-11 00:00:00', '2027-02-11 00:00:00', FALSE, FALSE, 7, 'Health'),
	(13, 'Digital Learning Project', 11000.00, 'Active', 'https://images.unsplash.com/photo-1516321318423-f06f85e504b3?w=800&q=70&auto=format&fit=crop', '2027-01-11 00:00:00', '2027-02-11 00:00:00', FALSE, FALSE, 8, 'Technology'),
	(14, 'Community Garden', 6500.00, 'Active', 'https://images.unsplash.com/photo-1416879595882-3373a0480b5b?w=800&q=70&auto=format&fit=crop', '2027-01-12 00:00:00', '2027-02-12 00:00:00', FALSE, FALSE, 9, 'Community'),
	(15, 'Emergency Relief Fund', 10000.00, 'Active', 'https://images.unsplash.com/photo-1469571486292-0ba58a3f068b?w=800&q=70&auto=format&fit=crop', '2027-01-12 00:00:00', '2027-02-12 00:00:00', FALSE, FALSE, 10, 'Community');
    
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
    
ALTER TABLE user CHANGE COLUMN passwordHASH password VARCHAR(250);

#passwords are stored as PBKDF2-SHA256 hashes (werkzeug generate_password_hash).
#plain-text test passwords are listed on the login page.
UPDATE user SET password = 'pbkdf2:sha256:260000$9IyzriilVOAJ2LX8$6d4d3d136eab370dc43967769cc39bbe079881ad838bb6a8304d10935d434c38' WHERE id = 1;
UPDATE user SET password = 'pbkdf2:sha256:260000$krIPJoPYSSeBHDCt$85f63500a1fd01ab74e80ce3e459473bac1fc38fb04b6a3cf612534ea13b4a46' WHERE id = 2;
UPDATE user SET password = 'pbkdf2:sha256:260000$nNK3uHsBWWcZcgKw$c52553f5a03b5d32ec9c83163ac2759a3812b45f9e20923de33d4db8f06b3e14' WHERE id = 3;
UPDATE user SET password = 'pbkdf2:sha256:260000$4484RYt2Rnyo24RW$6101ee0362e7811a8654da95d643334a0a91f57b2b132aa972793b9c52f6eca9' WHERE id = 4;
UPDATE user SET password = 'pbkdf2:sha256:260000$6FjeQHkr5Gfi46Us$6d99c900a252e19566c42fae9592524f900172145fbdcf69a9a67003d2f3c5bd' WHERE id = 5;
UPDATE user SET password = 'pbkdf2:sha256:260000$u3Llq3ZRYSZrPDSI$58d39da2dbfeed276a793c1b9ec62ef6d130cce0c8c0323a8c826189c0ad9712' WHERE id = 6;
UPDATE user SET password = 'pbkdf2:sha256:260000$INOcgM3NAQOWQDCN$658549c5b5aefc0bbde8ef28382cf60b4137aefb86495fc191cde58b52f5af6c' WHERE id = 7;
UPDATE user SET password = 'pbkdf2:sha256:260000$bEfM76yqNNK1DZtE$041fe9dffbadf0c44038e8f78d960f848682a50e7e0f62085b6408ef7221d847' WHERE id = 8;
UPDATE user SET password = 'pbkdf2:sha256:260000$ArBx3oinlOWDsYTb$b4cc0b32a416b8540f0431ce1878c5ff5f4c12563a9aa8a8ec7202add220262a' WHERE id = 9;
UPDATE user SET password = 'pbkdf2:sha256:260000$kpEHTCdNuFsHeAut$f0bc97aec0e972dd50dc12d05dea9b6ccb6e24be7d8e7707478a97498895f4c1' WHERE id = 10;
UPDATE user SET password = 'pbkdf2:sha256:260000$5YF1bg8KJVs34dcF$b0582486e343a33e81d8284658110741e05a2abf8aa2e23fc98e6d1294f6b1e1' WHERE id = 11;
UPDATE user SET password = 'pbkdf2:sha256:260000$v7VZ7NAyHaI6jKhF$fdad4b2a8c9e8fcf706e5be56d0ffd06d3ff67f6fd23ca6c61fa834f49c29026' WHERE id = 12;
UPDATE user SET password = 'pbkdf2:sha256:260000$zWzSV1mmGDaDsNvD$b53e99fb23af13539eb5480d36370982d328509d29cdc09e82dfe9ca76ccbb01' WHERE id = 13;
UPDATE user SET password = 'pbkdf2:sha256:260000$VsLxWqOHemXc4cFb$e32e30e31ea4e94441e6310349bc3b5764cc9357edbc40b218d83b59f339d369' WHERE id = 14;
UPDATE user SET password = 'pbkdf2:sha256:260000$EVl6b1QhApamoGQ9$47ae7214897142974f2333120ecbf3cae45f9bcaa9bb9b261a743386e2c16dfc' WHERE id = 15;

#CAMPAIGN DETAIL PAGE ADDITIONS
#campaign description (fundraising purpose and goals)
ALTER TABLE campaign ADD COLUMN description TEXT AFTER title;

#donor details captured by the donation form (A1 design: full name, address, email, tier, payment method, message)
ALTER TABLE donation
    ADD COLUMN donorName VARCHAR(100) NOT NULL DEFAULT '' AFTER amount,
    ADD COLUMN donorEmail VARCHAR(100) AFTER donorName,
    ADD COLUMN donorAddress VARCHAR(255) AFTER donorEmail,
    ADD COLUMN message VARCHAR(500) AFTER donorAddress,
    ADD COLUMN tierID INT AFTER message,
    ADD FOREIGN KEY (tierID) REFERENCES subscriptionTier(id) ON DELETE SET NULL ON UPDATE CASCADE; #SET NULL keeps the donation if a tier is removed

UPDATE campaign SET description = 'Building wells in rural communities so families have safe drinking water close to home. Every $500 funds a hand pump that serves around 200 people.' WHERE id = 1;
UPDATE campaign SET description = 'Funding the recording, mixing and cover art for an independent album, with early access and behind-the-scenes sessions for supporters.' WHERE id = 2;
UPDATE campaign SET description = 'Covering venue and travel costs for a free community tech summit with live podcast recordings and founder Q&A sessions.' WHERE id = 3;
UPDATE campaign SET description = 'Developing affordable VR headsets for classrooms so students can take virtual field trips to museums, labs and historic sites.' WHERE id = 4;
UPDATE campaign SET description = 'Emergency food and medical kits for families affected by monsoon flooding in northern India.' WHERE id = 5;
UPDATE campaign SET description = 'Back-to-school packs with books, stationery and bags for 500 students in low-income areas.' WHERE id = 6;
UPDATE campaign SET description = 'Stocking local food banks with fresh produce and pantry staples through the winter months.' WHERE id = 7;
UPDATE campaign SET description = 'Training teachers and supplying learning materials for village schools without reliable funding.' WHERE id = 8;
UPDATE campaign SET description = 'Free coaching, equipment and tournament fees for kids who cannot afford club sport.' WHERE id = 9;
UPDATE campaign SET description = 'Installing water filtration systems in schools and clinics where tap water is unsafe to drink.' WHERE id = 10;
UPDATE campaign SET description = 'A free weekend festival showcasing local artists, live murals and workshops for all ages.' WHERE id = 11;
UPDATE campaign SET description = 'Helping patients cover the cost of treatment, medication and travel to specialist appointments.' WHERE id = 12;
UPDATE campaign SET description = 'Laptops, internet access and coding lessons for students learning from home.' WHERE id = 13;
UPDATE campaign SET description = 'Turning an empty lot into a shared garden where neighbours grow fresh food together.' WHERE id = 14;
UPDATE campaign SET description = 'Rapid-response funding for shelter, water and supplies when disasters strike.' WHERE id = 15;

#creator bios shown on the campaign page
UPDATE creator SET bio = 'Grammy-winning artist and producer sharing behind-the-scenes studio sessions with fans.' WHERE id = 6;
UPDATE creator SET bio = 'The All-In Podcast: four besties talking tech, markets and philanthropy every week.' WHERE id = 7;
UPDATE creator SET bio = 'Tech reviewer known for crisp, honest videos on the latest gadgets and how they help people learn.' WHERE id = 8;
UPDATE creator SET bio = 'Creator behind some of the biggest philanthropy videos online, funding real projects around the world.' WHERE id = 9;
UPDATE creator SET bio = 'Storyteller, entrepreneur and Beta Squad member raising money for clean water and disaster relief.' WHERE id = 10;

#tiers for the creators that had none
INSERT INTO subscriptionTier (id, tierName, price, description, creatorID) VALUES
	(6, 'Stan', 5.00, 'Join the community Discord', 8),
	(7, 'Member', 15.00, 'Early access to reviews', 8),
	(8, 'Superfan', 30.00, 'Monthly live Q&A', 8),
	(9, 'Stan', 5.00, 'Shoutout in the credits', 9),
	(10, 'Member', 15.00, 'Behind the scenes videos', 9),
	(11, 'Superfan', 30.00, 'Vote on the next project', 9),
	(12, 'Stan', 5.00, 'Join WhatsApp group', 10),
	(13, 'Member', 15.00, 'Behind the scenes content', 10),
	(14, 'Superfan', 30.00, 'Free merch and a Facetime call', 10);

#donor details for the existing donations
UPDATE donation SET amount = 30.00, donorName = 'Lara', donorEmail = 'lara@email.com', donorAddress = '12 King St, Brisbane QLD', message = 'Been watching you since I was a kid. This is my way of saying thank you!', tierID = 14 WHERE transactionID = 1;
UPDATE donation SET amount = 15.00, donorName = 'Jade', donorEmail = 'jade@email.com', donorAddress = '4 Ann St, Brisbane QLD', message = 'Cannot wait to hear the album!', tierID = 2 WHERE transactionID = 2;
UPDATE donation SET amount = 15.00, donorName = 'Emma', donorEmail = 'emma@email.com', donorAddress = '88 George St, Sydney NSW', message = 'See you at the summit.', tierID = 4 WHERE transactionID = 3;
UPDATE donation SET amount = 5.00, donorName = 'Tessa', donorEmail = 'tessa@email.com', donorAddress = '9 Queen St, Melbourne VIC', message = 'Inspiring to see you stand up for what is right.', tierID = 12 WHERE transactionID = 4;
UPDATE donation SET amount = 50.00, donorName = 'Maya', donorEmail = 'maya@email.com', donorAddress = '21 Adelaide St, Brisbane QLD', message = 'Love the new direction, keep going!', tierID = NULL WHERE transactionID = 5;

#more donations so each active campaign has some history
INSERT INTO donation (amount, donorName, donorEmail, donorAddress, message, tierID, paymentNetwork, transactionDate, status, customerID, campaignID) VALUES
	(100.00, 'Jade', 'jade@email.com', '4 Ann St, Brisbane QLD', 'Clean water changes everything. Happy to help.', NULL, 'Visa', '2027-01-08 10:15:00', 'Done', 2, 1),
	(15.00, 'Lara', 'lara@email.com', '12 King St, Brisbane QLD', 'Your travel series was amazing!', 13, 'Mastercard', '2027-01-10 09:00:00', 'Done', 1, 10),
	(250.00, 'Emma', 'emma@email.com', '88 George St, Sydney NSW', 'For the school filters.', NULL, 'Apple Pay', '2027-01-11 14:30:00', 'Done', 3, 10),
	(40.00, 'Tessa', 'tessa@email.com', '9 Queen St, Melbourne VIC', 'Every kid deserves the right supplies.', NULL, 'Visa', '2027-01-09 08:45:00', 'Done', 4, 6),
	(30.00, 'Maya', 'maya@email.com', '21 Adelaide St, Brisbane QLD', 'Great cause, love the pod.', 5, 'Mastercard', '2027-01-09 19:20:00', 'Done', 5, 7),
	(20.00, 'Lara', 'lara@email.com', '12 King St, Brisbane QLD', NULL, NULL, 'PayPal', '2027-01-10 12:00:00', 'Done', 1, 7),
	(15.00, 'Jade', 'jade@email.com', '4 Ann St, Brisbane QLD', 'Your reviews got me into coding.', 7, 'Visa', '2027-01-12 16:10:00', 'Done', 2, 13),
	(60.00, 'Emma', 'emma@email.com', '88 George St, Sydney NSW', 'Laptops for students, yes please.', NULL, 'Mastercard', '2027-01-12 17:40:00', 'Done', 3, 13),
	(30.00, 'Tessa', 'tessa@email.com', '9 Queen St, Melbourne VIC', 'Sport kept me out of trouble growing up.', 11, 'Apple Pay', '2027-01-10 11:05:00', 'Done', 4, 9);

#updates for more campaigns
INSERT INTO campaign_post (campaignID, title, content, postDate) VALUES
	(1, 'First well completed', 'The first hand pump is live and already serving the village school. Thank you to everyone who donated!', '2027-01-15'),
	(10, 'Filters arrived', 'The first shipment of filtration units has arrived and installation starts next week.', '2027-01-14'),
	(6, 'Packing day', 'Volunteers packed 120 school bags today. 380 to go!', '2027-01-13'),
	(7, 'Food bank restocked', 'Your donations filled two pantries this week with fresh fruit and vegetables.', '2027-01-12'),
	(13, '25 laptops delivered', 'The first 25 laptops went out to students this morning, each with a year of internet access.', '2027-01-16'),
	(9, 'Season kicks off', 'Thanks to you, 40 kids took to the field for their first training session.', '2027-01-14');


#ADMIN DASHBOARD ADDITIONS
#suspended accounts cannot log in (new registrations do not need approval, so there is no "pending" user state)
ALTER TABLE user ADD COLUMN isSuspended BOOLEAN NOT NULL DEFAULT FALSE;

#content reported as inappropriate or misleading. Sample reports are added here by hand (no public reporting form)
create table report(
    id INT AUTO_INCREMENT PRIMARY KEY,
    campaignID INT NOT NULL,
    reporterID INT, #the user who reported it, kept as NULL if that account is later deleted
    reason VARCHAR(100) NOT NULL,
    details TEXT,
    status VARCHAR(20) NOT NULL DEFAULT 'Open', #Open, Resolved or Dismissed
    reportedAt DATETIME DEFAULT current_timestamp,
    reviewedAt DATETIME,
    foreign key(campaignID) references campaign(id) on delete cascade on update cascade,
    foreign key(reporterID) references user(id) on delete set null on update cascade
);

INSERT INTO report (campaignID, reporterID, reason, details, status, reportedAt, reviewedAt) VALUES
	(5, 1, 'Misleading fundraising goal', 'The goal amount does not match what the description says the money is for.', 'Open', '2027-01-09 10:00:00', NULL),
	(1, 3, 'Spam in comments', 'Supporter message on Water Project is advertising a crypto giveaway.', 'Open', '2027-01-12 15:30:00', NULL),
	(4, 2, 'Inappropriate image', 'Campaign banner looks like it was copied from another brand.', 'Open', '2027-01-13 09:45:00', NULL),
	(11, 4, 'Possible duplicate campaign', 'Looks very similar to another arts festival campaign.', 'Dismissed', '2027-01-10 11:20:00', '2027-01-11 08:00:00');


#CREATOR DASHBOARD ADDITIONS
#optional image on a campaign update (uploaded files are saved under static/img/uploads/)
ALTER TABLE campaign_post ADD COLUMN postImage VARCHAR(255) AFTER content;
#campaign status values used by the app: Pending, Active, Paused, Closed (set by the creator once approved),
#Rejected and Suspended (set by an admin only)


#FEATURED SECTION: creator photo + tagline shown on the homepage "Today's Top Featured" cards
ALTER TABLE creator
    ADD COLUMN tagline VARCHAR(150) AFTER bio,
    ADD COLUMN profileImage VARCHAR(255) AFTER tagline;

UPDATE creator SET tagline = 'Experience behind the scenes', profileImage = 'https://upload.wikimedia.org/wikipedia/en/4/46/Drake_-_Toosie_Slide.png' WHERE id = 6;
UPDATE creator SET tagline = 'Chat with besties on the pod', profileImage = 'https://cdn.prod.website-files.com/633cd7641794e536812c0e29/66dd7f9c930b82790d33fefc_Copy_of_All-In_Logos_3_600x.png' WHERE id = 7;
UPDATE creator SET tagline = 'More reviews on latest technology', profileImage = 'https://i.ytimg.com/vi/idEAABFzpfg/maxresdefault.jpg' WHERE id = 8;
UPDATE creator SET tagline = 'Philanthropy at the biggest scale', profileImage = 'https://mrbeast.store/cdn/shop/files/Hero-Desktop.png?v=1762185908&width=1200' WHERE id = 9;
UPDATE creator SET tagline = 'Storytelling with a purpose', profileImage = 'https://shopndl.com/cdn/shop/files/1Q4A2840.jpg?v=1762270409&width=1200' WHERE id = 10;

#homepage "Today's Top Featured": Drake (Music Album), All-In (Community Food Relief), MKBHD (Digital Learning Project)
UPDATE campaign SET isFeatured = (id IN (2, 7, 13));
