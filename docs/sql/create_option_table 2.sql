-- Creates the options table used to store candidates for events
-- NOTE: `option` is a reserved keyword; we must use backticks.

CREATE TABLE IF NOT EXISTS `option` (
  `option_id` INT NOT NULL AUTO_INCREMENT,
  `option_text` VARCHAR(255) NOT NULL,
  `option_event_id` INT NOT NULL,
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`option_id`),
  KEY `idx_option_event_id` (`option_event_id`),
  CONSTRAINT `fk_option_event`
    FOREIGN KEY (`option_event_id`) REFERENCES `event`(`event_id`)
    ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;