var gulp = require('gulp');
var exec = require('child_process').exec;
var bs = require('browser-sync').create();

gulp.task('browser-sync', [], function() {
    bs.init({
        server: {
            baseDir: "./_build/html"
        }
    });
});

gulp.task('make-html', function (cb) {
  exec('make html', function (err, stdout, stderr) {
    console.log(stdout);
    console.log(stderr);
    cb(err);
  });
});

gulp.task('watch', ['browser-sync'], function () {
    gulp.watch("*.rst", ['make-html']);
    gulp.watch("**/*.html").on('change', bs.reload);
});
