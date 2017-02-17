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
            if(data.success){
                if(data.data && !$.isEmptyObject(data.data))
                    dfd.resolve(data.data);
                else
                    dfd.reject("No data returned " + data.message);
            }else{
                dfd.reject(data.message);
            }
        }).fail(function(jqXHR, textStatus){
            dfd.reject("Error " + textStatus);
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
            if(data.success){
                dfd.resolve(data.data);
            }else{
                dfd.reject(data.message);
            }
        }).fail(function(jqXHR, textStatus){
            dfd.reject("Error " + textStatus);
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
    }
};
