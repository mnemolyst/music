var express = require('express');
var router = express.Router();
var requirejs = require('requirejs');
var mongo = require('mongodb').MongoClient;
var ObjectId = require('mongodb').ObjectID;
var childProcess = require('child_process');

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

            res.type('application/json');
            res.send(JSON.stringify(doc));

            db.close();
        });
    });
});

router.post('/composition/:id?', function(req, res, next) {
    mongo.connect(mongoUrl, function(err, db) {
        if (req.params.id === undefined) {
            db.collection('composition').insertOne(
                req.body,
                {},
                function(err, r) {
                    if (! err && r.result.ok === 1) {
                        res.status(201).send(r.insertedId);
                    } else  {
                        //console.log(err);
                        res.sendStatus(500);
                    }
                    db.close();
                }
            );
        } else {
            db.collection('composition').replaceOne(
                {_id: new ObjectId(req.params.id)},
                req.body,
                {},
                function(err, r) {
                    if (! err && r.result.ok === 1) {
                        res.status(201).send(String(r.modifiedCount));
                    } else {
                        res.sendStatus(500);
                    }
                    db.close();
                }
            );
        }
    });
});

router.post('/suggest', function(req, res, next) {
    console.log(req.body);
    //var returnData = childProcess.spawnSync(
    //    'python',
    //    ['midiKeras.py', 'predict'],
    //    { input: req.body.
    //);
    //child.stdin.end(prototxt[idx]);
    res.sendStatus(200);
});

module.exports = router;
