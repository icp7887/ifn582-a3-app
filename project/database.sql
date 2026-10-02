DROP DATABASE IF EXISTS app_db;
CREATE DATABASE app_db;
USE app_db;

CREATE TABLE Campaign (
    id INT PRIMARY KEY,
    title VARCHAR(150) NOT NULL,
    goalAmount DECIMAL(10,2) NOT NULL,
    status VARCHAR(30) NOT NULL,
    campaignImage VARCHAR(255),
    startDate DATE NOT NULL,
    endDate DATE NOT NULL,
    isFeatured BOOLEAN DEFAULT FALSE,
    isFlagged BOOLEAN DEFAULT FALSE,
    creatorID INT NOT NULL,
    category VARCHAR(50) NOT NULL
);

INSERT INTO Campaign
(id, title, goalAmount, status, campaignImage, startDate, endDate, isFeatured, isFlagged, creatorID, category)
VALUES
(1, 'Water Project', 10000.00, 'Active', 'charity.png', '2027-01-07', '2027-02-07', TRUE, FALSE, 10, 'Community'),
(2, 'Music Album', 50000.00, 'Active', 'music-album.png', '2027-01-07', '2027-02-07', TRUE, FALSE, 6, 'Arts'),
(3, 'All-in Summit', 500.00, 'Pending', 'banner.png', '2027-01-07', '2027-02-07', TRUE, FALSE, 7, 'Technology'),
(4, 'VR Glasses', 3000.00, 'Pending', 'vr.png', '2027-01-07', '2027-02-07', FALSE, FALSE, 8, 'Technology'),
(5, 'India Fund', 2000.00, 'Pending', 'india.png', '2027-01-07', '2027-02-07', FALSE, TRUE, 9, 'Community'),
(6, 'School Supplies Drive', 7500.00, 'Active', 'school.png', '2027-01-08', '2027-02-08', FALSE, FALSE, 6, 'Education'),
(7, 'Community Food Relief', 12000.00, 'Active', 'food.png', '2027-01-08', '2027-02-08', FALSE, FALSE, 7, 'Community'),
(8, 'Rural Education Fund', 8500.00, 'Active', 'education.png', '2027-01-09', '2027-02-09', FALSE, FALSE, 8, 'Education'),
(9, 'Youth Sports Program', 9000.00, 'Active', 'sports.png', '2027-01-09', '2027-02-09', FALSE, FALSE, 9, 'Community'),
(10, 'Clean Water Initiative', 15000.00, 'Active', 'water.png', '2027-01-10', '2027-02-10', FALSE, FALSE, 10, 'Community'),
(11, 'Local Arts Festival', 6000.00, 'Active', 'arts.png', '2027-01-10', '2027-02-10', FALSE, FALSE, 6, 'Arts'),
(12, 'Medical Support Fund', 13000.00, 'Active', 'medical.png', '2027-01-11', '2027-02-11', FALSE, FALSE, 7, 'Health'),
(13, 'Digital Learning Project', 11000.00, 'Active', 'digital.png', '2027-01-11', '2027-02-11', FALSE, FALSE, 8, 'Technology'),
(14, 'Community Garden', 6500.00, 'Active', 'garden.png', '2027-01-12', '2027-02-12', FALSE, FALSE, 9, 'Community'),
(15, 'Emergency Relief Fund', 10000.00, 'Active', 'emergency.png', '2027-01-12', '2027-02-12', FALSE, FALSE, 10, 'Community');

CREATE TABLE CampaignPost (
    id INT PRIMARY KEY AUTO_INCREMENT,
    campaignID INT NOT NULL,
    title VARCHAR(150) NOT NULL,
    content TEXT NOT NULL,
    postDate DATE NOT NULL,
    FOREIGN KEY (campaignID) REFERENCES Campaign(id)
);

INSERT INTO CampaignPost
(campaignID, title, content, postDate)
VALUES
(1, 'Water Project Update', 'We have started work on the water project and preparations are underway.', '2027-01-15'),
(2, 'Music Album Progress', 'Recording for the new music album is currently underway.', '2027-01-16'),
(3, 'All-in Summit Update', 'Planning and preparation for the All-in Summit have begun.', '2027-01-17');