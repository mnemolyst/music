var exec = require('child_process').exec;

exec('ls -l', function(err, stdout) {
    console.log(stdout);
});
