function getBookInitials(title) {
  return title
    .trim()
    .split(/\s+/)
    .slice(0, 2)
    .map((word) => word[0])
    .join('')
    .toUpperCase()
}

function BookCover({ book }) {
  return (
    <span className={`book-cover cover-${book.id % 5}`} aria-hidden="true">
      <span>{getBookInitials(book.title)}</span>
      {book.image && <img src={book.image} alt="" loading="lazy" onError={(event) => { event.currentTarget.remove() }} />}
    </span>
  )
}

export default BookCover
