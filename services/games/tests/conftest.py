import pytest


@pytest.fixture
def client():
    from src import app

    app.app.config['TESTING'] = True
    
    app.db.engine.execute('DROP TABLE IF EXISTS `game`;')
    
    app.db.engine.execute('''CREATE TABLE `game` (
  `game_id` int NOT NULL AUTO_INCREMENT,
  `title` varchar(64) NOT NULL,
  `platform` varchar(10) NOT NULL,
  `price` float NOT NULL,
  `stock` int NOT NULL,
  PRIMARY KEY (`game_id`)
) ENGINE=InnoDB AUTO_INCREMENT=10 DEFAULT CHARSET=utf8;''')

    app.db.engine.execute('''INSERT INTO `game` VALUES (1,'Final Fantasy VI','SNES',40,15),(2,'Legend of Zelda Skyward Sword','Switch',60.5,200),(3,'Skies of Arcadia','GameCube',18.7,1),(7,'Phantasy Star IV','Mega Drive',25.55,5),(9,'Mario is Missing','MS-DOS',100,1);''')

    return app.app.test_client()