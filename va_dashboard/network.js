module.exports = {
    get: function(url, token, data){
        var opts = {
            type: 'GET',
            url: url
        };
        if(typeof token !== 'undefined') {
            opts.headers = {'Authorization': 'Token ' + token};
        }
        if(typeof data !== 'undefined') {
            opts.data = data;
        }
        return $.ajax(opts);
    },
    post: function(url, token, data){
        var opts = {
            type: 'POST',
            url: url
        };

        if(typeof token !== 'undefined') {
            opts.headers = {'Authorization': 'Token ' + token};
        }

        if(typeof data !== 'undefined') {
            opts.contentType =  'application/json';
            opts.data = JSON.stringify(data);
        }

        return $.ajax(opts);
    }
};
