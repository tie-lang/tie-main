; ModuleID = 'tie'
source_filename = "input.tie"

declare i32 @printf(ptr, ...)

declare i64 @strlen(ptr)
declare i32 @strcmp(ptr, ptr)
declare ptr @malloc(i64)
declare void @llvm.memcpy.p0.p0.i64(ptr, ptr, i64, i1)

declare ptr @fopen(ptr, ptr)
declare i64 @fwrite(ptr, i64, i64, ptr)
declare i32 @fclose(ptr)
declare i32 @fflush(ptr)
declare void @exit(i32)
declare i32 @remove(ptr)
declare double @sqrt(double)
declare double @sin(double)
declare double @cos(double)
declare double @tan(double)
declare double @exp(double)
declare double @log(double)
declare double @pow(double, double)
declare double @floor(double)
declare double @ceil(double)
declare double @round(double)


define i64 @main() {
entry:
%1 = alloca ptr
%2 = alloca ptr
%3 = call i32 (ptr, ...) @printf(ptr @.str.2, ptr @.str.1)
br label %loop.cond.2
loop.cond.2:
br i1 true, label %loop.body.3, label %loop.exit.4
loop.body.3:
%5 = call i32 (ptr, ...) @printf(ptr @.str.4, ptr @.str.3)
%7 = call i32 @fflush(ptr null)
%8 = call ptr @tie_read_line()
store ptr %8, ptr %1
%9 = load ptr, ptr %1
%10 = call i32 @strcmp(ptr %9, ptr @.str.5)
%11 = icmp eq i32 %10, 0
br i1 %11, label %if.then.12, label %if.else.13
if.then.12:
ret i64 0
if.else.13:
br label %if.merge.14
if.merge.14:
%12 = load ptr, ptr %1
%13 = call i32 @strcmp(ptr %12, ptr @.str.6)
%14 = icmp ne i32 %13, 0
br i1 %14, label %if.then.18, label %if.else.19
if.then.18:
%15 = load ptr, ptr %1
%16 = call ptr @tie_eval_expr(ptr %15)
store ptr %16, ptr %2
%17 = load ptr, ptr %2
%18 = call i32 @strcmp(ptr %17, ptr @.str.7)
%19 = icmp ne i32 %18, 0
br i1 %19, label %if.then.27, label %if.else.28
if.then.27:
%20 = load ptr, ptr %2
%21 = call i32 (ptr, ...) @printf(ptr @.str.2, ptr %20)
br label %if.merge.29
if.else.28:
%23 = call i32 (ptr, ...) @printf(ptr @.str.2, ptr @.str.8)
br label %if.merge.29
if.merge.29:
br label %if.merge.20
if.else.19:
br label %if.merge.20
if.merge.20:
br label %loop.cond.2
loop.exit.4:
ret i64 0
}


@.str.1 = private unnamed_addr constant [34 x i8] c"tie REPL\EF\BC\88\E8\BE\93\E5\85\A5 :quit \E9\80\80\E5\87\BA\EF\BC\89\00"
@.str.2 = private unnamed_addr constant [4 x i8] c"%s\0A\00"
@.str.3 = private unnamed_addr constant [3 x i8] c"> \00"
@.str.4 = private unnamed_addr constant [3 x i8] c"%s\00"
@.str.5 = private unnamed_addr constant [6 x i8] c":quit\00"
@.str.6 = private unnamed_addr constant [1 x i8] c"\00"
@.str.7 = private unnamed_addr constant [1 x i8] c"\00"
@.str.8 = private unnamed_addr constant [1 x i8] c"\00"
declare ptr @tie_read_line()
declare ptr @tie_eval_expr(ptr)
declare void @tie_free_result(ptr)
