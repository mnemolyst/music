var mongo =         require('mongodb').MongoClient;
var mongoUrl = process.env.MONGO_URL || 'mongodb://localhost:27017/music';

mongo.connect(mongoUrl, function(err, db) {
    db.collection('composition').remove({}, {}, function(err, r) {
        db.collection('composition').insertMany([
            {
                name: 'one',
                notes: [
                    {
                        pitch: 440,
                        duration: 1,
                    },
                    {
                        pitch: 880,
                        duration: 1,
                    },
                    {
                        pitch: 660,
                        duration: 1,
                    },
                ],
            },
            {
                name: 'two',
                notes: [
                ],
            },
        ], function(err, r) {
            if (err) throw err;
            db.close();
        });
    });
});
