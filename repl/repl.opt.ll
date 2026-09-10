; ModuleID = 'F:\Projects\tie-repo\tie-main\repl\repl.ll'
source_filename = "input.tie"

@.str.1 = private unnamed_addr constant [34 x i8] c"tie REPL\EF\BC\88\E8\BE\93\E5\85\A5 :quit \E9\80\80\E5\87\BA\EF\BC\89\00"
@.str.3 = private unnamed_addr constant [3 x i8] c"> \00"
@.str.4 = private unnamed_addr constant [3 x i8] c"%s\00"
@.str.5 = private unnamed_addr constant [6 x i8] c":quit\00"

; Function Attrs: nofree nounwind
declare noundef i32 @printf(ptr noundef readonly captures(none), ...) local_unnamed_addr #0

; Function Attrs: mustprogress nocallback nofree nounwind willreturn memory(argmem: read)
declare i32 @strcmp(ptr captures(none), ptr captures(none)) local_unnamed_addr #1

; Function Attrs: nofree nounwind
declare noundef i32 @fflush(ptr noundef captures(none)) local_unnamed_addr #0

define noundef i64 @main() local_unnamed_addr {
entry:
  %puts = tail call i32 @puts(ptr nonnull dereferenceable(1) @.str.1)
  %0 = tail call i32 (ptr, ...) @printf(ptr nonnull dereferenceable(1) @.str.4, ptr nonnull @.str.3)
  %1 = tail call i32 @fflush(ptr null)
  %2 = tail call ptr @tie_read_line()
  %3 = tail call i32 @strcmp(ptr noundef nonnull dereferenceable(1) %2, ptr noundef nonnull dereferenceable(6) @.str.5)
  %4 = icmp eq i32 %3, 0
  br i1 %4, label %if.then.12, label %if.merge.14

if.then.12:                                       ; preds = %if.merge.20, %entry
  ret i64 0

if.merge.14:                                      ; preds = %entry, %if.merge.20
  %5 = phi ptr [ %9, %if.merge.20 ], [ %2, %entry ]
  %strcmpload = load i8, ptr %5, align 1
  %.not = icmp eq i8 %strcmpload, 0
  br i1 %.not, label %if.merge.20, label %if.then.18

if.then.18:                                       ; preds = %if.merge.14
  %6 = tail call ptr @tie_eval_expr(ptr nonnull %5)
  %strcmpload5 = load i8, ptr %6, align 1
  %.not6 = icmp eq i8 %strcmpload5, 0
  br i1 %.not6, label %if.else.28, label %if.then.27

if.then.27:                                       ; preds = %if.then.18
  %puts8 = tail call i32 @puts(ptr nonnull dereferenceable(1) %6)
  br label %if.merge.20

if.else.28:                                       ; preds = %if.then.18
  %putchar = tail call i32 @putchar(i32 10)
  br label %if.merge.20

if.merge.20:                                      ; preds = %if.merge.14, %if.then.27, %if.else.28
  %7 = tail call i32 (ptr, ...) @printf(ptr nonnull dereferenceable(1) @.str.4, ptr nonnull @.str.3)
  %8 = tail call i32 @fflush(ptr null)
  %9 = tail call ptr @tie_read_line()
  %10 = tail call i32 @strcmp(ptr noundef nonnull dereferenceable(1) %9, ptr noundef nonnull dereferenceable(6) @.str.5)
  %11 = icmp eq i32 %10, 0
  br i1 %11, label %if.then.12, label %if.merge.14
}

declare ptr @tie_read_line() local_unnamed_addr

declare ptr @tie_eval_expr(ptr) local_unnamed_addr

; Function Attrs: nofree nounwind
declare noundef i32 @puts(ptr noundef readonly captures(none)) local_unnamed_addr #0

; Function Attrs: nofree nounwind
declare noundef i32 @putchar(i32 noundef) local_unnamed_addr #0

attributes #0 = { nofree nounwind }
attributes #1 = { mustprogress nocallback nofree nounwind willreturn memory(argmem: read) }
