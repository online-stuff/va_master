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
        $.ajax(opts).done(function(data){
            if(data.message)
                dfd.resolve(data.message);
            else
                dfd.resolve(data.data);
        }).fail(function(jqXHR){
            dfd.reject(jqXHR.responseJSON.message);
        });
        return dfd.promise();
    },
    post: function(url, token, data){
        var dfd = new $.Deferred();
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
        $.ajax(opts).done(function(data){
            if(data.message)
                dfd.resolve(data.message);
            else
                dfd.resolve(data.data);
        }).fail(function(jqXHR){
            dfd.reject(jqXHR.responseJSON.message);
        });

        return dfd.promise();
    },
    put: function(url, token, data){
        var dfd = new $.Deferred();
        var opts = {
            type: 'PUT',
            url: url
        };

        if(typeof token !== 'undefined') {
            opts.headers = {'Authorization': 'Token ' + token};
        }

        if(typeof data !== 'undefined') {
            opts.contentType =  'application/json';
            opts.data = JSON.stringify(data);
        }
        $.ajax(opts).done(function(data){
            if(data.message)
                dfd.resolve(data.message);
            else
                dfd.resolve(data.data);
        }).fail(function(jqXHR){
            dfd.reject(jqXHR.responseJSON.message);
        });

        return dfd.promise();
    },
    delete: function(url, token, data){
        var dfd = new $.Deferred();
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
        $.ajax(opts).done(function(data){
            dfd.resolve(data.data);
        }).fail(function(jqXHR){
            dfd.reject(jqXHR.responseJSON.message);
        });

        return dfd.promise();
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
