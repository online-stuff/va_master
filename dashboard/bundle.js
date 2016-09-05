var fs = require("fs");
var browserify = require('browserify');
var resolve = require('path').resolve;


browserify(resolve(__dirname, "app.js"))
  .transform(resolve(__dirname, "node_modules/babelify"), {presets: ["react"]})
  .bundle()
  .pipe(fs.createWriteStream(resolve(__dirname, "static/bundle.js")));
