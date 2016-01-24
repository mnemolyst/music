var express = require('express');
var router = express.Router();
var requirejs = require('requirejs');
var mongo =         require('mongodb').MongoClient;
var ObjectId =      require('mongodb').ObjectID;

var mongoUrl = process.env.MONGO_URL || 'mongodb://localhost:27017/music';

/* GET home page. */
router.get('/', function(req, res, next) {
    mongo.connect(mongoUrl, function(err, db) {
        db.collection('composition').find().sort({name: 1}).toArray(function(err, docs) {
            if (err) throw err;

            res.render('index', {
                compositions: docs,
            });

            db.close();
        });
    });
});

router.get('/compositions', function(req, res, next) {
    mongo.connect(mongoUrl, function(err, db) {
        db.collection('composition').find().sort({name: 1}).toArray(function(err, docs) {
            if (err) throw err;

            res.render('compositions', {
                compositions: docs,
            });

            db.close();
        });
    });
});

router.get('/composition/:id', function(req, res, next) {
    mongo.connect(mongoUrl, function(err, db) {
        db.collection('composition').find({_id: new ObjectId(req.params.id)}).limit(1).next(function(err, doc) {
            if (err) throw err;

            res.send(JSON.stringify(doc));

            db.close();
        });
    });
});

module.exports = router;
