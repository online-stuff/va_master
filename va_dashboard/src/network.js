module.exports = {
    get: function(url, token, data){
        var dfd = new $.Deferred();
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
    },
    delete: function(url, token, data){
        var opts = {
            type: 'DELETE',
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
    },
    post_file: function(url, token, data){
        var opts = {
            type: 'POST',
            url: url,
            processData: false,
            contentType: false,
            data: data
        };

        if(typeof token !== 'undefined') {
            opts.headers = {'Authorization': 'Token ' + token};
        }

        return $.ajax(opts);
    },
    download_file: function(url, token, data){
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
