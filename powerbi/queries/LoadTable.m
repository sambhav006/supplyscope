(file as text, types as list) as table =>
let
 Source = Csv.Document(File.Contents(RootPath & "\data\processed\" & file & ".csv"), [Delimiter=",", Encoding=65001, QuoteStyle=QuoteStyle.Csv]),
 Headers = Table.PromoteHeaders(Source, [PromoteAllScalars=true]),
 EmptyToNull = Table.ReplaceValue(Headers, "", null, Replacer.ReplaceValue, Table.ColumnNames(Headers)),
 Typed = Table.TransformColumnTypes(EmptyToNull, types, "en-US")
in Typed
