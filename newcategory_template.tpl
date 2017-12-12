<!doctype HTML>
<html>
<head>
    <title>Criar um novo post</title>
</head>
<body>
%if (username != None):
     {{username}} <a href="/logout">Logout</a> | <a href="/newpost">New Post</a> | <a href="/newcategory">New Category</a>
<p>
%end
<form action="/newcategory" method="POST">
    <h2>Nova Categoria</h2>
    <input type="text" name="category" size="120" value=""><br>
    <p>
        <input type="submit" value="Add">
    </p>
</form>

</body>
</html>