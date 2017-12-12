<!doctype HTML>
<html>
<head>
    <title>
        Blog Post
    </title>
</head>
<body>
<a href="/">Blog Home</a><br><br>

<h2>{{post['title']}}</h2>
Posted {{post['date']}}<i> By {{post['author']}}</i><br>
<p>
    <em>Category</em>:
    %if ('category' in post):
        <a href="/category/{{post['permalink_category']}}">{{post['category']}}</a>
    %end
<p>
<hr>
{{!post['body']}}
<p>
    <em>Filed Under</em>:
    %if ('tags' in post):
        %for tag in post['tags'][0:1]:
        <a href="/tag/{{tag}}">{{tag}}</a>
            %for tag in post['tags'][1:]:
            , <a href="/tag/{{tag}}">{{tag}}</a>
            %end
        %end
    %end
<p>
<ul>
    %if ('comments' in post):
        %numComments = len(post['comments'])
    %else:
        %numComments = 0
    %end
    %for i in range(0, numComments):
        Author: {{post['comments'][i]['author']}}<br>
        {{post['comments'][i]['body']}}<br>
        <hr>
    %end
    <h3>Add a comment</h3>
    <form action="/newcomment" method="POST">
        <input type="hidden" name="permalink", value="{{post['permalink']}}">
        {{errors}}
        <b>Nome</b> (obrigatorio)<br>
        <input type="text" name="commentName" size="60" value="{{comment['name']}}"><br>
        <b>Email</b> (opcional)<br>
        <input type="text" name="commentEmail" size="60" value="{{comment['email']}}"><br>
        <b>Comentario</b><br>
        <textarea name="commentBody" cols="60" rows="10">{{comment['body']}}</textarea><br>
        <input type="submit" value="Submit">
    </form>
</ul>
</body>
</html>