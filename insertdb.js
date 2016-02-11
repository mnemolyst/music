var mongo =         require('mongodb').MongoClient;
var mongoUrl = process.env.MONGO_URL || 'mongodb://localhost:27017/music';

mongo.connect(mongoUrl, function(err, db) {
    db.collection('composition').remove({}, {}, function(err, r) {
        db.collection('composition').insertMany([
            {
                name: 'one',
                notes: [
                    {
                        t: 0,
                        d: 1,
                        n: 0,
                    },
                    {
                        t: 0,
                        d: 1,
                        n: 12,
                    },
                    {
                        t: 0,
                        d: 1,
                        n: 6,
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
