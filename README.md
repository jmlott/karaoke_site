# karaoke_site
Python &amp; Flask webapp for maintaining a karaoke queue

This is hosted on www.pythonanywhere.com and utilizes Python 2.7 and Flask with a MySQL database. 

To use this as a template for your own site, you will need to create a database with a table called "songs" with the following attributes:

mysql> show create table songs;
+-------+------------------------------------------------------+
| Table | Create Table                                         |
+-------+------------------------------------------------------+
| songs | CREATE TABLE `songs` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `user` varchar(255) NOT NULL,
  `artist` varchar(255) NOT NULL,
  `title` varchar(255) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=159 DEFAULT CHARSET=utf8        |
+-------+------------------------------------------------------+

You will need to edit karaoke.py lines 16 - 27 to include your database info and admin account info.
