use meowny_db;

drop table if exists picfile;
drop table if exists commStats;
drop table if exists dataEntry;
drop table if exists user;

create table user (
   aid int auto_increment,
   name varchar(50) not null unique,
   password varchar(100),
   goal varchar(300),
   primary key (aid),
   INDEX (aid)
)
ENGINE = InnoDB;

create table picfile (
    aid int primary key,
    filename varchar(50),
    foreign key (aid) references user(aid) 
        on delete cascade 
        on update cascade
);
describe picfile;

create table dataEntry (
   aid int,
   dataTime timestamp,
   year_and_weekNum int,
   food_spending float,
   clothing_spending float,
   transp_spending float,
   entert_spending float,
   personal_spending float,
   miscel_spending float,
   total_spending float,
   primary key (dataTime),
   -- necessary for ref integ
   INDEX (aid),
   foreign key (aid) references user(aid)
       on update restrict
       on delete restrict
)
ENGINE = InnoDB;

create table commStats(
   year_and_weekNum int not null,
   total_avg float,  
   food_avg float,
   clothing_avg float, 
   transp_avg float,
   entert_avg float,
   personal_avg float,
   miscel_avg float,
   primary key (year_and_weekNum)
)
ENGINE = InnoDB;